# MVP requirements and acceptance criteria

## Approved scope

The owner approved a new PUBLIC `clebrsonn/subtitle-hub` repository, a Django/PostgreSQL subtitle site, and delegation to Jules. Start from subtitles the owner will prepare in a dedicated directory. AniDB metadata and AniDB/TMDB/TVDB identifiers are essential. The COMPLETE `Rapptz/jimaku` project is an explicitly approved reference; see `references/jimaku.md`. Preserve independent review and owner-only merge/deployment decisions.

## R1. Working, minimal application

Build a supported and pinned Django monolith with server-rendered templates, PostgreSQL, migrations, authenticated staff administration, catalogue and read/download API. Use database/local-file primitives rather than introducing Redis, Celery, a separate SPA or microservices. Background or CLI management commands are sufficient for imports and metadata enrichment. The application must run with metadata providers disabled/unconfigured and show the setup/pending state honestly.

## R2. Read-only source import

- A configurable source root is mounted read-only. No real owner path is needed during implementation. ASS, SSA and SRT are the initial allowed formats; do not accept archives, videos or public uploads.
- Provide preview/dry-run and real import commands with useful summaries. Ignore incomplete/changing files, reject symlinks and paths escaping the root, bound file sizes and validate subtitle structure/encoding without converting original bytes.
- Import into a separate managed store with generated safe storage keys. A download must still work after the source is removed or unavailable. Source files are never modified, moved, deleted or rewritten. Preserve ASS/SSA style/effect text as bytes.
- Repeated scans are idempotent. Deduplicate identical blobs by cryptographic content hash without collapsing distinct catalogue associations, releases or real revisions. Changed bytes create a new version, not silent replacement. Handle interrupted imports and concurrent scans safely; document recovery of incomplete/orphaned writes.
- An optional versioned JSON manifest can provide explicit IDs, language/variant, release and episode references using only confined relative paths. Document and validate its schema; use synthetic examples. Do not require a manifest for every file: uncertain filename/title identification can be reviewed manually.

## R3. Identities and episode relationships

- Keep stable internal identities separate from provider identities. AniDB `aid` is an anime/work ID; `eid` is an episode ID. Keep episode type and number, including specials/credits/trailers/parodies/other, without coercing all numbers into ordinary integer episodes.
- TMDB movie IDs and TV IDs are distinct namespaces. TVDB/TMDB series IDs are not episode IDs. Keep series, season, episode and ordering context explicitly.
- Support multiple AniDB works/cours mapping to seasons of one external TV series, explicit offsets, specials, one-to-many and many-to-one episode mappings. Do not fabricate a one-to-one mapping or equate numbers from different providers.
- Store source/provenance, retrieval/source revision, review status and confidence for imported mapping candidates. Approved manual mappings take precedence and must not be overwritten on refresh. Incomplete/conflicting mappings stay unresolved and visible to staff.
- Evaluate Anime-Lists as a metadata/mapping source. Document any supported subset and preserve unsupported mapping constructs as pending rather than silently misparsing. Cover real mapping shapes with small clearly identified synthetic fixtures. Do not vendor the full third-party dataset without checking its terms.

## R4. AniDB metadata without unnecessary traffic

- Read AniDB through supported API/dumps, not HTML scraping. Client name/version must be explicitly configured for a registered client, never copied from another application or invented as valid.
- Use local title search/cache and a title dump refresh no more than daily when enabled. Enrich only the works/episodes needed by the catalogue; no bulk database crawl.
- Persist metadata cache, default minimum cache TTL of24h and global request pacing of at least2s between requests. Support a conservative configurable daily budget, bounded retries and persistent cooldown on ban/rate-limit responses. Shared state must work across multiple worker processes.
- Parse AniDB error payloads even when HTTP status is200. Bound network timeouts, response and decompression size and disable XML external entities. Do not use FlareSolverr or retries to bypass quotas/bans.
- Public search and catalogue rendering must not call AniDB once per page/file or fan out to live providers. Network failures leave local records usable with enrichment pending.
- TMDB/TVDB direct enrichment is optional if mappings suffice. Any direct integrations need documented credentials/terms, caching, typed IDs, error handling and attribution. Missing credentials must not lead to fabricated metadata. AniList may be an optional future provider; it is not a replacement for the required AniDB/TMDB/TVDB mapping.

## R5. Catalogue, API and review

- Provide title/alternative-title search, works, episodes, available subtitle versions and download pages. Filter by language/variant (including pt-BR), format, full/forced/SDH metadata when known, episode and release. Unknown metadata stays unknown.
- API queries by explicit AniDB, TMDB and TVDB namespaces must return the correct matching catalogue entries, including multiple works linked to one external series. Unknown IDs return empty/not-found, not a title-guess substitute. Validate and document invalid/ambiguous ID combinations.
- Only approved/published records are publicly discoverable/downloadable. Staff can resolve pending matches, edit associations and publish/unpublish entries; anonymous users cannot administer/import or access unpublished files.
- Safe opaque download identifiers, attachment headers, escaped metadata, bounded/paginated queries and controlled resource usage. No local source paths, arbitrary filesystem access, user-supplied upstream URLs, credentials or session data in public output.
- Include source/author/release provenance and a simple contact/report mechanism for incorrect files and removal requests. The app must not claim uploaded/extracted subtitles automatically carry redistribution rights.

## R6. Tests and reproducible delivery

Use test-first vertical slices and preserve meaningful red/green evidence. At minimum cover:
1. Real PostgreSQL migrations and constraints.
2. Valid SRT/ASS/SSA import and identical-byte downloads.
3. Dry-run with no persisted/file mutation; stable source files unchanged.
4. Re-import idempotency, blob deduplication, multiple associations and changed-file revisions.
5. Traversal, symlinks, malformed manifests/files, size limits, incomplete copy and concurrent imports.
6. Pending ambiguous title/episode matching and staff-only review/publication.
7. AniDB cache hits, shared pacing, configured daily budget, error XML in HTTP200, cooldown and missing registration.
8. Typed TMDB movies versus TV; TVDB/TMDB offsets, specials, many-to-many episodes and manual override preservation.
9. Search by all three provider identities; shared external series mapped to multiple works.
10. Catalogue/filter/detail/download browser E2E path plus anonymous admin/unpublished-file denial.

External API tests use local fixture HTTP servers or mocks; CI must not hit real AniDB/TMDB/TVDB. Label fixtures as synthetic/recorded and never report fixture success as live validation. Exercise the actual PostgreSQL application and actual packaged image, not only mocked services. Add a repeatable smoke command using a disposable PostgreSQL instance, synthetic data, import, ID search and identical-byte download.

## R7. Operations, documentation and acceptance gates

- Dockerfile and Compose: separate source:ro, managed files and database storage; sane resource defaults, loopback-bound local access, non-root app, health/readiness checks, controlled migrations, no committed secrets or production default admin credentials.
- Clear installation/configuration commands, manifest examples, API documentation, backup/restore steps for metadata AND managed blobs, rollback notes, upstream setup/terms/attribution and operational limits.
- README index, Mermaid trust/data-flow diagram and ADRs explaining chosen architecture, identity/mapping strategy, cache/rate policy, storage/import safety and Jimaku comparison.
- A pull request with implementation and executed test/build/smoke results, exact commands and limitations. Do not silently delete acceptance tests or mark incomplete work done.
- No owner real data, deployment, merge, changes to other repositories/services or global software-license selection. Hermes performs independent validation after the PR is ready; the owner decides final merge/deployment.
