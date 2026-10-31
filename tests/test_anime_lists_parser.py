import pytest
from django.core.management import call_command
from catalogue.models import Work, ExternalMapping
from pathlib import Path

@pytest.fixture
def mock_anime_list_xml(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<anime-list>
    <anime anidbid="1234" tvdbid="5678" tmdbid="91011" defaulttvdbseason="1">
        <name>Mock Anime</name>
        <mapping anidbseason="1" tvdbseason="1" />
        <mapping anidbseason="2" tvdbseason="2" offset="12" />
    </anime>
</anime-list>
"""
    file_path = tmp_path / "anime-list.xml"
    file_path.write_text(xml_content)
    return file_path

@pytest.mark.django_db
def test_parse_anime_lists(mock_anime_list_xml):
    call_command('parse_anime_lists', str(mock_anime_list_xml))

    # Check that it created a work and mappings
    anidb_mapping = ExternalMapping.objects.get(provider='anidb', external_id="1234")
    work = anidb_mapping.work

    assert ExternalMapping.objects.filter(work=work, provider='tvdb', external_id="5678").exists()
    assert ExternalMapping.objects.filter(work=work, provider='tmdb', external_id="91011").exists()

    # Check that the unsupported complex constructs were added as PENDING anime-lists mappings
    unsupported_mappings = ExternalMapping.objects.filter(work=work, provider='anime-lists')
    assert unsupported_mappings.count() == 2

    mapping_with_offset = unsupported_mappings.filter(raw_data__offset="12").first()
    assert mapping_with_offset is not None
    assert mapping_with_offset.status == 'pending'
