# Subtitle Hub MVP

A Django/PostgreSQL monolith application for cataloging and safely sharing Anime subtitles.

## Documentation Index
- [Architecture & Boundaries](docs/architecture.md)
- [Requirements](docs/requirements.md)
- [ADR 0001: Small Monolith](docs/adr/0001-small-monolith.md)
- [ADR 0002: Identities](docs/adr/0002-identities-and-mappings.md)
- [Jimaku Reference Notes](docs/references/jimaku.md)

## Operator Setup and Requirements

The application runs using Docker Compose. Ensure `docker` and `docker-compose` are installed.

1. **Environment Configuration**: Create a `.env` file at the root:
    ```
    DEBUG=False
    SECRET_KEY=your-secure-secret-key
    ANIDB_CLIENT_NAME=your_registered_client
    ANIDB_CLIENT_VERSION=1
    ANIDB_PACING_SECONDS=2
    ANIDB_DAILY_BUDGET=500
    ```
2. **Directory Permissions**: Prepare the managed media directory for the non-root user:
    ```bash
    mkdir -p managed_media source_media
    sudo chown -R 1000:1000 managed_media
    ```
3. **Build and Run**:
    ```bash
    docker-compose up -d --build
    ```
4. **Database Initialization** (Migrations run automatically. Create an admin):
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

## Subtitle Import Flow

1. Place your valid subtitle files (`.ass`, `.srt`, `.ssa`) in the `source_media/` directory. (Optionally include a `manifest.json` for explicit metadata matching).
2. Run a dry run to verify paths:
    ```bash
    docker-compose exec web python manage.py import_subtitles --dry-run
    ```
3. Run the import:
    ```bash
    docker-compose exec web python manage.py import_subtitles
    ```
4. Imported entries will default to `Pending` status. Log in to the staff interface (`/admin/`) to approve mappings, set them to `Published`, and assign them to catalog Works.

## Metadata Enrichment
```bash
# Fetch AniDB metadata respecting pacing bounds
docker-compose exec web python manage.py enrich_metadata
```

## Backup and Restore

- **Database**:
    ```bash
    # Backup
    docker-compose exec db pg_dump -U hub_user -d subtitle_hub > backup.sql
    # Restore
    cat backup.sql | docker-compose exec -T db psql -U hub_user -d subtitle_hub
    ```
- **Files**: Back up the `managed_media/` directory.

## Trust Boundaries
- The source directory (`source_media`) is mounted as read-only.
- All files are fingerprinted via SHA-256 and copied into a safe `managed_media` storage.
- Download URLs do not expose the internal path and safely stream immutable blobs.
- Public users cannot download `Pending` files.
