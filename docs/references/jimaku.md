# Complete Jimaku repository as a reference

The owner explicitly approved using the ENTIRE project as a reference, beyond `src/anilist.rs`.

- Repository: https://github.com/Rapptz/jimaku
- Reference commit inspected: `59f60ed10c441259cdabe9577819ad2df85c6164`
- Upstream license reported by GitHub and verified in LICENSE: AGPL-3.0.
- Scope here: design/reference study, not a fork or wholesale code transplant. Direct copying/reuse requires a separate documented licensing decision; do not assume a public new repository removes upstream obligations.

## Required study by the implementation agent

Read the upstream README, LICENSE and relevant concrete code end-to-end. At minimum examine:

- Catalogue and models: `src/models.rs`, `src/database.rs`, `src/routes/entry.rs`, relevant entry/index templates.
- Files and downloads: `src/download.rs`, import/admin entry paths, storage/trash handling and access checks.
- Metadata: `src/anilist.rs`, `src/tmdb.rs`, `src/relations.rs` and associated models/routes.
- API: route definitions and `templates/api_description.md` / API templates.
- Staff/user boundaries: `src/auth.rs`, `src/token.rs`, `src/key.rs`, admin/auth/audit/report routes.
- Operational behavior: `src/config.rs`, `src/cached.rs`, `src/ratelimit.rs`, `src/error.rs` and state handling.

Record which mechanisms were actually read, what informed the independent implementation, differences and limitations. Do not copy all features into the MVP merely because the full repository is a reference. Scrapers, Discord integration, public uploads and optional cloud/file-host integrations are not requested.

## Metadata distinction

The inspected `anilist.rs` queries AniList GraphQL by ID or title, returns romaji/English/native title variants and media format, and handles a Retry-After header. These are useful provider-client concerns, but AniList IDs are not AniDB IDs and this code does not implement the requested AniDB/TMDB/TVDB episode mapping. Implement bounded robust error handling rather than blindly copying upstream retry behavior.

## Other primary references

- AniDB API overview: https://wiki.anidb.net/w/API
- AniDB HTTP API definition: https://wiki.anidb.net/w/HTTP_API_Definition
- Mapping format: https://github.com/Anime-Lists/anime-lists/blob/master/README.md
- TMDB external IDs: https://developer.themoviedb.org/reference/tv-series-external-ids
- Upload/input safety: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

AniDB wiki fetches can be blocked. Use official API documentation/indexed copies with declared provenance, not HTML scraping or quota bypass. Runtime access still requires operator registration/configuration; fixture tests are not real-service validation.
