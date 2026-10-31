import json
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from catalogue.models import Work, ExternalMapping
from pathlib import Path

class Command(BaseCommand):
    help = 'Parse Anime-Lists XML format to establish TMDB/TVDB mappings for AniDB works.'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Path to the anime-list.xml file')

    def handle(self, *args, **options):
        file_path = Path(options['file']).resolve()

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File {file_path} not found."))
            return

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f"Invalid XML: {e}"))
            return

        # Basic parsing loop for the Anime-Lists format (anime-list.xml)
        for anime in root.findall('anime'):
            anidbid = anime.get('anidbid')
            tvdbid = anime.get('tvdbid')
            tmdbid = anime.get('tmdbid')

            if not anidbid:
                continue

            # For the MVP, we just find or create a work based on the AniDB ID
            mapping, created = ExternalMapping.objects.get_or_create(
                provider='anidb',
                external_id=anidbid,
                defaults={'status': ExternalMapping.Status.PENDING}
            )

            work = mapping.work
            if not work:
                work = Work.objects.create(title=f"Unknown AniDB {anidbid}")
                mapping.work = work
                mapping.save()

            # Create TVDB mapping if present
            if tvdbid:
                ExternalMapping.objects.get_or_create(
                    work=work,
                    provider='tvdb',
                    external_id=tvdbid,
                    defaults={'status': ExternalMapping.Status.PENDING}
                )

            # Create TMDB (TV default) mapping if present
            if tmdbid:
                ExternalMapping.objects.get_or_create(
                    work=work,
                    provider='tmdb',
                    media_kind='tv',
                    external_id=tmdbid,
                    defaults={'status': ExternalMapping.Status.PENDING}
                )

            # Store unsupported complex constructs in raw_data (e.g. mapping overrides)
            # The Anime-Lists format uses elements like <mapping> or <supplement> inside <anime>
            # We explicitly handle unsupported rules by placing them in `pending` status.
            mappings_node = anime.findall('mapping')
            if mappings_node:
                for rule in mappings_node:
                    # E.g. <mapping anidbseason="1" tvdbseason="2" />
                    rule_dict = {k: v for k, v in rule.attrib.items()}

                    ExternalMapping.objects.create(
                        work=work,
                        provider='anime-lists',
                        media_kind='unknown',
                        external_id='',
                        status=ExternalMapping.Status.PENDING,
                        raw_data=rule_dict
                    )

        self.stdout.write(self.style.SUCCESS("Anime-Lists parsing complete."))
