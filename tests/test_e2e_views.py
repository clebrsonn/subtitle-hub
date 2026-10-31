import pytest
from django.urls import reverse
from catalogue.models import Work, SubtitleBlob, SubtitleEntry, ExternalMapping
from django.contrib.auth.models import User

@pytest.fixture
def test_data(db):
    work = Work.objects.create(title="E2E Anime")
    ExternalMapping.objects.create(work=work, provider="anidb", external_id="123")
    ExternalMapping.objects.create(work=work, provider="tmdb", media_kind="tv", external_id="456")

    blob = SubtitleBlob.objects.create(sha256="abcd", storage_key="abcd.ass", byte_size=1024, format="ass")
    # Published entry
    SubtitleEntry.objects.create(work=work, blob=blob, language="pt-BR", status=SubtitleEntry.Status.PUBLISHED, original_filename="ep1.ass")
    # Pending entry
    SubtitleEntry.objects.create(work=work, blob=blob, language="en", status=SubtitleEntry.Status.PENDING, original_filename="ep1_en.ass")

    User.objects.create_superuser('admin', 'admin@example.com', 'password')
    return work, blob

@pytest.mark.django_db
def test_catalogue_search_anidb(client, test_data):
    work, blob = test_data
    # Search by AniDB ID
    response = client.get(reverse('search'), {'anidb': '123'})
    assert response.status_code == 200
    assert work.title in str(response.content)

@pytest.mark.django_db
def test_catalogue_search_tmdb_tv(client, test_data):
    work, blob = test_data
    # Search by TMDB TV ID
    response = client.get(reverse('search'), {'tmdb_tv': '456'})
    assert response.status_code == 200
    assert work.title in str(response.content)

@pytest.mark.django_db
def test_catalogue_public_hides_pending(client, test_data):
    work, blob = test_data
    # Detail page should only show published files
    response = client.get(reverse('work_detail', args=[work.id]))
    assert response.status_code == 200
    assert "ep1.ass" in str(response.content)
    assert "ep1_en.ass" not in str(response.content) # Pending

@pytest.mark.django_db
def test_download_published_file(client, test_data, tmp_path, settings):
    work, blob = test_data
    d = tmp_path / "managed_media"
    d.mkdir()
    settings.MANAGED_MEDIA_ROOT = str(d)

    test_file = d / blob.storage_key
    test_file.write_text("subtitle content")

    published_entry = SubtitleEntry.objects.get(language="pt-BR")

    response = client.get(reverse('download', args=[published_entry.id]))
    assert response.status_code == 200
    assert response['Content-Disposition'] == f'attachment; filename="{published_entry.original_filename}"'
    assert b"".join(response.streaming_content) == b"subtitle content"

@pytest.mark.django_db
def test_download_pending_file_denied(client, test_data):
    work, blob = test_data
    pending_entry = SubtitleEntry.objects.get(language="en")

    # Anonymous user denied
    response = client.get(reverse('download', args=[pending_entry.id]))
    assert response.status_code == 403

    # Admin allowed
    client.login(username='admin', password='password')
    # It would hit 500/404 because file isn't on disk in this test, but not 403
    response = client.get(reverse('download', args=[pending_entry.id]))
    assert response.status_code != 403
