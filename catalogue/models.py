from django.db import models

class Work(models.Model):
    """Internal identity for a series/movie."""
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Episode(models.Model):
    """Internal identity for an episode with typed number/kind."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="episodes")
    episode_number = models.CharField(max_length=50) # e.g. "1", "S1", "C1"
    episode_type = models.CharField(max_length=50, default="regular") # regular, special, credit, trailer, parody, other
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.work.title} - {self.episode_type} {self.episode_number}"

class ExternalMapping(models.Model):
    """
    Provenance-aware mapping to AniDB (aid/eid), TMDB (movie/tv), TVDB.
    Supports multiple AniDB works mapped to one external series, and episode mappings.
    """
    class Status(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        PENDING = 'pending', 'Pending'
        REJECTED = 'rejected', 'Rejected'

    work = models.ForeignKey(Work, on_delete=models.CASCADE, null=True, blank=True, related_name="external_mappings")
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True, related_name="external_mappings")

    provider = models.CharField(max_length=50) # anidb, tmdb, tvdb, anime-lists
    media_kind = models.CharField(max_length=50, blank=True) # movie, tv, unknown
    external_id = models.CharField(max_length=255)

    # For episodes, we might have external season/episode numbers for mappings (like offsets)
    external_season = models.CharField(max_length=50, blank=True)
    external_episode = models.CharField(max_length=50, blank=True)

    is_manual_override = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)

    confidence = models.FloatField(null=True, blank=True)
    source_revision = models.CharField(max_length=255, blank=True)
    retrieval_time = models.DateTimeField(auto_now_add=True)

    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        target = self.episode or self.work
        return f"{self.provider}:{self.external_id} -> {target}"

class SubtitleBlob(models.Model):
    """Immutable managed subtitle blobs."""
    sha256 = models.CharField(max_length=64, unique=True)
    storage_key = models.CharField(max_length=255, unique=True)
    byte_size = models.BigIntegerField()
    format = models.CharField(max_length=20) # srt, ass, ssa
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.format} - {self.sha256[:8]}"

class SubtitleEntry(models.Model):
    """Catalog entry linking a SubtitleBlob to a Work/Episode."""
    class Status(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        PENDING = 'pending', 'Pending'
        REJECTED = 'rejected', 'Rejected'

    blob = models.ForeignKey(SubtitleBlob, on_delete=models.CASCADE, related_name="entries")
    work = models.ForeignKey(Work, on_delete=models.SET_NULL, null=True, blank=True, related_name="subtitle_entries")
    episode = models.ForeignKey(Episode, on_delete=models.SET_NULL, null=True, blank=True, related_name="subtitle_entries")

    language = models.CharField(max_length=50) # e.g. pt-BR
    release_group = models.CharField(max_length=255, blank=True)
    is_forced = models.BooleanField(default=False)
    is_sdh = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.language})"

class AniDBState(models.Model):
    """
    Persisted state to enforce cross-process pacing and budgets.
    """
    id = models.IntegerField(primary_key=True, default=1)
    last_request_at = models.DateTimeField(null=True, blank=True)
    daily_request_count = models.IntegerField(default=0)
    current_date = models.DateField(auto_now_add=True)

    is_banned = models.BooleanField(default=False)
    cooldown_until = models.DateTimeField(null=True, blank=True)

    # Metadata sync status
    last_title_dump_sync = models.DateTimeField(null=True, blank=True)
