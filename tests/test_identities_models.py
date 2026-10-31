import pytest
from django.core.exceptions import ValidationError
from catalogue.models import Work, Episode, ExternalMapping

@pytest.mark.django_db
def test_external_mapping_many_to_many_and_offsets():
    # Multiple AniDB works mapped to one TVDB/TMDB series, offsets, specials.

    # 1. Create two AniDB Works (e.g. Season 1 and Season 2)
    work1 = Work.objects.create(title="Anime S1")
    work2 = Work.objects.create(title="Anime S2")

    # 2. Map both to a single TMDB TV series
    mapping1 = ExternalMapping.objects.create(
        work=work1,
        provider="tmdb",
        media_kind="tv",
        external_id="12345",
        is_manual_override=True
    )
    mapping2 = ExternalMapping.objects.create(
        work=work2,
        provider="tmdb",
        media_kind="tv",
        external_id="12345",
        is_manual_override=True
    )

    assert ExternalMapping.objects.filter(provider="tmdb", external_id="12345").count() == 2

    # 3. Create Episodes with typed numbers (including specials/offsets)
    ep_s1_e1 = Episode.objects.create(work=work1, episode_number="1", episode_type="regular")
    ep_s1_sp1 = Episode.objects.create(work=work1, episode_number="S1", episode_type="special")
    ep_s2_e1 = Episode.objects.create(work=work2, episode_number="1", episode_type="regular")

    # 4. Map them with offsets. TMDB might consider ep_s2_e1 as Season 2, Episode 1.
    ExternalMapping.objects.create(
        episode=ep_s2_e1,
        provider="tmdb",
        media_kind="tv",
        external_id="12345",
        external_season="2",
        external_episode="1"
    )

    # Ensure typed episode numbers are preserved
    assert ep_s1_sp1.episode_number == "S1"

@pytest.mark.django_db
def test_pending_anime_lists_parsing_unsupported():
    work = Work.objects.create(title="Complex Anime")

    # Simulate an unsupported mapping construct from Anime-Lists (e.g., a mapping rule we don't fully parse yet)
    mapping = ExternalMapping.objects.create(
        work=work,
        provider="anime-lists",
        media_kind="unknown",
        external_id="",
        status="pending",
        raw_data={"complex_rule": "some_value_we_dont_understand"}
    )

    assert mapping.status == "pending"
    assert mapping.raw_data["complex_rule"] == "some_value_we_dont_understand"
