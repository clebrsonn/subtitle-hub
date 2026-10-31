import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from catalogue.models import AniDBState
from catalogue.anidb import AniDBClient, AniDBError

@pytest.fixture
def override_anidb_settings(settings):
    settings.ANIDB_CLIENT_NAME = "testclient"
    settings.ANIDB_CLIENT_VERSION = "1"
    settings.ANIDB_PACING_SECONDS = 2
    settings.ANIDB_DAILY_BUDGET = 5
    yield settings

@pytest.mark.django_db
def test_anidb_pacing_and_budget(override_anidb_settings):
    client = AniDBClient()

    # Simulate a request by taking budget and pacing token
    assert client._can_make_request() is True
    client._record_request()

    # Second request immediately should be blocked by pacing
    assert client._can_make_request() is False

    # Advance state to allow another request
    state = AniDBState.objects.get()
    state.last_request_at = timezone.now() - timedelta(seconds=override_anidb_settings.ANIDB_PACING_SECONDS + 1)
    state.save()

    assert client._can_make_request() is True

    # Exhaust the budget
    state.daily_request_count = override_anidb_settings.ANIDB_DAILY_BUDGET
    state.save()
    assert client._can_make_request() is False

@pytest.mark.django_db
def test_anidb_xml_error_in_http200(override_anidb_settings, requests_mock):
    client = AniDBClient()

    # Mock HTTP 200 but error in XML (simulated BANNED or 500 equivalent)
    xml_error = b'<?xml version="1.0" encoding="utf-8"?><error>BANNED</error>'
    requests_mock.get('https://api.anidb.net:9001/httpapi', content=xml_error, status_code=200)

    # Bypass pacing lock for test
    state, _ = AniDBState.objects.get_or_create(id=1)
    state.last_request_at = timezone.now() - timedelta(hours=1)
    state.save()

    with pytest.raises(AniDBError) as excinfo:
        client.fetch_anime(1)

    assert "BANNED" in str(excinfo.value)

    # Verify cooldown was applied
    state.refresh_from_db()
    assert state.is_banned is True

@pytest.mark.django_db
def test_anidb_missing_registration_fails_gracefully(settings):
    settings.ANIDB_CLIENT_NAME = ""
    settings.ANIDB_CLIENT_VERSION = ""

    client = AniDBClient()
    assert client.is_configured() is False

    with pytest.raises(AniDBError) as excinfo:
        client.fetch_anime(1)

    assert "Client not registered" in str(excinfo.value)
