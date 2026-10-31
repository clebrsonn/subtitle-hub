import pytest
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from catalogue.models import Work, ExternalMapping, AniDBState

@pytest.fixture
def override_anidb_settings(settings):
    settings.ANIDB_CLIENT_NAME = "testclient"
    settings.ANIDB_CLIENT_VERSION = "1"
    settings.ANIDB_PACING_SECONDS = 0  # Disable pacing for test speed
    settings.ANIDB_DAILY_BUDGET = 500
    yield settings

@pytest.mark.django_db
def test_enrich_metadata_command(override_anidb_settings, requests_mock):
    # Setup test data
    work = Work.objects.create(title="Old Title")
    mapping = ExternalMapping.objects.create(
        work=work,
        provider='anidb',
        external_id="123"
    )
    # the default creates it with now() so let's explicitly update it
    # and bypass auto_now_add via update()
    ExternalMapping.objects.filter(id=mapping.id).update(retrieval_time=timezone.now() - timedelta(days=2))

    # Mock HTTP response
    xml_response = b'<?xml version="1.0" encoding="utf-8"?><anime><title type="main">New Enriched Title</title></anime>'
    requests_mock.get('https://api.anidb.net:9001/httpapi', content=xml_response, status_code=200)

    # Run command
    call_command('enrich_metadata')

    # Verify title was updated and retrieval time was refreshed
    mapping.refresh_from_db()
    work.refresh_from_db()

    assert work.title == "New Enriched Title"
    assert mapping.retrieval_time > timezone.now() - timedelta(minutes=5)
