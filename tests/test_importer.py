import pytest
import os
import hashlib
from unittest.mock import patch
from django.core.management import call_command
from django.conf import settings
from catalogue.models import SubtitleBlob, SubtitleEntry

@pytest.fixture
def managed_dir(tmp_path):
    d = tmp_path / "managed_media"
    d.mkdir()
    with patch.object(settings, 'MANAGED_MEDIA_ROOT', str(d)):
        yield d

@pytest.fixture
def source_dir(tmp_path):
    d = tmp_path / "source_media"
    d.mkdir()

    # Valid file
    file1 = d / "test1.ass"
    file1.write_text("Style: Default,Arial,20,&H00FFFFFF\nDialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Hello")

    # Valid file duplicate bytes
    file2 = d / "test2.ass"
    file2.write_text("Style: Default,Arial,20,&H00FFFFFF\nDialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Hello")

    # Changed bytes for new version test
    file3 = d / "test3.srt"
    file3.write_text("1\n00:00:00,000 --> 00:00:05,000\nHello World\n")

    # Manifest
    manifest = d / "manifest.json"
    manifest.write_text('{"test1.ass": {"language": "en", "is_forced": true}}')

    # Symlink escaping root
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("secret")
    os.symlink(str(outside_file), str(d / "bad_link.ass"))

    with patch.object(settings, 'SOURCE_MEDIA_ROOT', str(d)):
        yield d


@pytest.mark.django_db
def test_import_dry_run(source_dir, managed_dir):
    call_command('import_subtitles', '--dry-run')

    # Should not persist any blobs or copy files
    assert SubtitleBlob.objects.count() == 0
    assert not list(managed_dir.glob("*"))


@pytest.mark.django_db
def test_import_real_run_deduplication(source_dir, managed_dir):
    call_command('import_subtitles')

    # 3 files processed, but 2 share the same bytes
    assert SubtitleBlob.objects.count() == 2

    # Should have entries for both files pointing to the same blob
    entries = SubtitleEntry.objects.all()
    assert entries.count() == 3

    blob1 = SubtitleBlob.objects.get(format='ass')
    ass_entries = entries.filter(blob=blob1)
    assert ass_entries.count() == 2

    # Manifest correctly parsed for test1.ass
    entry1 = ass_entries.get(original_filename="test1.ass")
    assert entry1.language == "en"
    assert entry1.is_forced is True

    # Should reject the symlink
    assert not entries.filter(original_filename="bad_link.ass").exists()

@pytest.mark.django_db
def test_import_idempotency_and_changed_bytes(source_dir, managed_dir):
    call_command('import_subtitles')
    assert SubtitleBlob.objects.count() == 2

    # Run again, should be idempotent
    call_command('import_subtitles')
    assert SubtitleBlob.objects.count() == 2

    # Change file3 bytes
    file3 = source_dir / "test3.srt"
    file3.write_text("1\n00:00:00,000 --> 00:00:05,000\nHello Changed World\n")

    call_command('import_subtitles')

    # Should create a new blob for the changed bytes
    assert SubtitleBlob.objects.count() == 3

    # And there should be a new entry for test3.srt, older ones might still exist or we might supersede them,
    # but let's assert there's at least the new one.
    entries = SubtitleEntry.objects.filter(original_filename="test3.srt")
    assert entries.count() == 2
