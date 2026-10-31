# Subtitle Hub

A subtitle catalogue and sharing application focused on anime, imported from an operator-managed directory. AniDB anime and episode identities are linked to explicitly typed TMDB and TVDB references without assuming identical episode numbering.

## Status

**Implementation specification, not a working application yet.** The initial commit contains requirements and architecture only. Runtime and test instructions must be added and exercised by the implementation PR.

## Initial scope

- Django monolith, PostgreSQL, server-rendered catalogue and read/download API.
- Read-only source-directory imports of ASS, SSA and SRT subtitles; managed copies preserve original bytes.
- AniDB metadata client with persistent caching, bounded request pacing, configurable budgets and backoff.
- Versioned/provenance-aware AniDB, TMDB and TVDB mappings, including episode offsets, specials and non-1:1 relationships.
- Administration and explicit review of uncertain matches; no public uploads in the MVP.
- Docker Compose, automated tests and operational documentation.

Repository visibility does not authorize publication of any subtitle or third-party dataset. No production configuration, real subtitle collection or credentials belong in this repository.

## Documentation

- [Requirements and acceptance criteria](docs/requirements.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [ADR 0001: a small Django monolith](docs/adr/0001-small-monolith.md)
- [ADR 0002: identities and episode mapping](docs/adr/0002-identities-and-mappings.md)
- [Agent contribution rules](AGENTS.md)

## Delivery gates

Jules implements on a separate branch and opens a pull request. Hermes independently reviews the exact delivered commit and exercises it locally. Merge, deployment and publication of real data require the owner's subsequent approval. Do not auto-merge or deploy.

No project-wide software license has been selected yet. Document third-party licenses separately; do not relicense imported data as application code.
