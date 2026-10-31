import os
import hashlib
import json
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from catalogue.models import SubtitleBlob, SubtitleEntry

ALLOWED_EXTENSIONS = {'.srt', '.ass', '.ssa'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class Command(BaseCommand):
    help = 'Import subtitles from configured source directory into managed storage.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the importer without making database changes or copying files.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        source_dir = Path(settings.SOURCE_MEDIA_ROOT).resolve()
        managed_dir = Path(settings.MANAGED_MEDIA_ROOT).resolve()

        if not source_dir.exists():
            self.stdout.write(self.style.ERROR(f"Source directory {source_dir} does not exist."))
            return

        if not dry_run:
            managed_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = source_dir / 'manifest.json'
        manifest = {}
        if manifest_path.exists() and manifest_path.is_file() and not manifest_path.is_symlink():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not read manifest.json: {e}"))

        processed = 0
        new_blobs = 0
        new_entries = 0

        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root).resolve()

            # Prevent path traversal outside root
            if not str(root_path).startswith(str(source_dir)):
                continue

            for file_name in files:
                file_path = (root_path / file_name)

                # Reject symlinks entirely for safety
                if file_path.is_symlink() or not file_path.is_file():
                    continue

                # Check extension
                ext = file_path.suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue

                # Check size
                try:
                    file_size = file_path.stat().st_size
                except Exception:
                    continue

                if file_size == 0 or file_size > MAX_FILE_SIZE:
                    continue

                processed += 1

                # Compute SHA-256
                sha256_hash = hashlib.sha256()
                try:
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(chunk)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error reading {file_path}: {e}"))
                    continue

                file_hash = sha256_hash.hexdigest()
                format_clean = ext[1:]

                # Safe managed path
                storage_key = f"{file_hash}{ext}"
                managed_file_path = managed_dir / storage_key

                rel_path = str(file_path.relative_to(source_dir))
                manifest_data = manifest.get(rel_path, {})
                language = manifest_data.get('language', 'unknown')
                is_forced = manifest_data.get('is_forced', False)

                if dry_run:
                    self.stdout.write(f"[Dry Run] Found {rel_path} -> {file_hash}")
                    continue

                try:
                    with transaction.atomic():
                        blob, created = SubtitleBlob.objects.get_or_create(
                            sha256=file_hash,
                            defaults={
                                'storage_key': storage_key,
                                'byte_size': file_size,
                                'format': format_clean
                            }
                        )

                        if created:
                            new_blobs += 1
                            # Atomic copy using shutil.copyfile, avoiding interrupted writes if possible
                            # Writing to temp then rename is safer.
                            temp_path = managed_file_path.with_suffix('.tmp')
                            try:
                                shutil.copyfile(file_path, temp_path)
                                temp_path.rename(managed_file_path)
                            except Exception as e:
                                raise Exception(f"Error copying to managed storage: {e}")

                        # Create SubtitleEntry if one for this file/blob doesn't exist
                        entry, entry_created = SubtitleEntry.objects.get_or_create(
                            blob=blob,
                            original_filename=file_name,
                            defaults={
                                'language': language,
                                'is_forced': is_forced,
                                'status': SubtitleEntry.Status.PENDING # Needs manual review
                            }
                        )

                        if entry_created:
                            new_entries += 1
                        elif entry.language != language or entry.is_forced != is_forced:
                            # Existing entry for the exact blob/filename but manifest metadata changed
                            entry.language = language
                            entry.is_forced = is_forced
                            entry.save()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Skipping {file_name}: {e}"))
                    continue

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete. Checked {processed} files."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Import complete. Processed {processed} files. Created {new_blobs} new blobs and {new_entries} new entries."
            ))
