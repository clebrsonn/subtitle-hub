# Agent contribution rules

## Scope and authority

Read `docs/requirements.md`, architecture and ADRs before changing code. The owner approved a PUBLIC repository and a Django/PostgreSQL MVP imported from their own prepared subtitle directory. Implementation belongs on a feature branch and in a pull request. Do not merge, deploy, publish real subtitle files, configure the owner's infrastructure, or access private accounts/collections. The existing `otakuhana` repository is unrelated and must not be modified.

Hermes owns independent review and validation of the exact delivered SHA. A coding agent's green test report does not establish independent acceptance.

## Implementation discipline

- Deliver a working application, not a plan-only PR, mock backend, placeholder endpoint, or disabled test suite.
- Use a small Django monolith, PostgreSQL and ordinary server-rendered templates. No separate SPA, microservices, vector database, Redis/Celery, or mandatory external AI service for this MVP.
- Use supported, pinned Python/Django/database dependencies and document the selected versions. Keep schema migrations in version control.
- Apply test-first vertical slices: execute a failing behavior test, implement minimally, run it green, then refactor. Include evidence of meaningful red/green cycles in PR notes. External-provider network calls are mocked/fixture-backed in CI; these tests must never be reported as live provider validation.
- CI must exercise the real PostgreSQL schema, not only SQLite. Provide and exercise a repeatable smoke test covering import -> catalogue/API -> identical-byte download.
- Include a reproducible container build, migrations and health/readiness checks. Database ports and application exposure must be loopback/private by default, not all interfaces. Fail closed for production secrets, host validation and administrative authentication.

## Data and identity

- Source import directories are read-only. Do not rename, rewrite, delete or convert source subtitles. Copy validated bytes into a separate managed store before making downloads available; downloads cannot depend on files remaining in the source directory.
- AniDB anime `aid` and episode `eid` are different identifiers. Episode numbers are typed strings, not always integers. TMDB movie and TV namespaces must be distinct. External IDs are not interchangeable across providers.
- Multiple AniDB works may map to different seasons of one TVDB/TMDB series, and episode relationships can be many-to-many. Do not impose a one-to-one external-series-ID constraint on internal works. Preserve offsets, specials, provenance and explicit manual overrides.
- Do not guess uncertain matches into published entries. An optional explicit metadata manifest and review screen must resolve ambiguity. Keep the import useful when provider access is unavailable, with enrichment marked pending.

## Upstream access

- Use AniDB's documented API and supported title dump, never HTML scraping or FlareSolverr to defeat its quotas.
- AniDB client name/version are operator configuration, not invented credentials or another application's registered client. Missing registration must result in a clear setup/pending state.
- Cache anime data persistently (at least 24h by default), pace globally at no more than one request per two seconds, support a conservative configurable daily budget and honor bans/backoff. Do not re-fetch a dataset repeatedly on the same day or bulk-crawl AniDB.
- Public search uses the local catalogue/cache. An ordinary webpage request must not fan out into upstream APIs.
- Handle HTTP errors AND error payloads returned inside HTTP200 XML/GraphQL responses. Bound timeouts, retries, responses, decompression and XML parsing; disable external entities.
- Document sources, retrieval timestamps, upstream licenses and attribution. Do not vendor an external database until its redistribution conditions have been checked.

## Security and public-repository hygiene

- No real subtitles, production manifests, filesystem paths, private network topology, API keys, passwords, cookies, tokens, database exports, or secrets in Git or PR logs. All samples and tests must be clearly synthetic or permissively licensed with attribution.
- Import only configured subtitle formats with bounded size/content parsing. Reject escaping paths, symlinks and path traversal, including manifest paths and download requests. Do not execute subtitle content or trust client MIME/filenames.
- Use opaque download IDs, safe generated storage keys, attachment response headers and escaped display text. Do not expose raw source paths or arbitrary server paths/URLs.
- No public upload endpoint in this MVP. Administrative edits and imports require appropriate authorization. Public reads expose only explicitly published/approved entries.
- Do not add a project-wide license on the owner's behalf. The owner explicitly approved the ENTIRE `Rapptz/jimaku` repository as a reference, not only `src/anilist.rs`. Study its catalogue, file handling, schema/models, relations/TMDB and AniList clients, API, administration, authentication, caching and rate limiting; document the relevant comparisons in `docs/references/jimaku.md`. This does not automatically import every upstream feature into the MVP. Jimaku remains a design/reference example, not permission to copy its AGPL code into an independently licensed application. Any proposed direct reuse requires a documented owner decision first.

## Required handoff

The PR must include tested setup commands, test results and limitations, a README documentation index, architecture/trust-boundary diagram, ADRs and API/import-manifest documentation. State which integrations were exercised with fixtures versus live registered access. Do not label incomplete acceptance criteria as done.
