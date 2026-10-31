# Reference: Jimaku Project

This document outlines the evaluation of the `Rapptz/jimaku` repository, as explicitly requested by the owner. The goal of this review was to study its concepts to inspire the architecture of the `subtitle-hub` MVP without committing to a full code transplant, given its AGPL-3.0 license.

- Reference commit inspected: `59f60ed10c441259cdabe9577819ad2df85c6164`

## Observations and Adopted Concepts

1. **Architecture & Scope**: Jimaku is a sophisticated Rust-based web application with features like Discord integration, extensive AniList/TMDB syncing, and user file uploads. For this MVP, we explicitly constrained our stack to a Django monolithic application and omitted features like user uploads and automatic metadata fetching, opting for operator-driven imports and a manual review boundary instead.
2. **Metadata Modeling**:
    - Jimaku stores external relations carefully, often handling multiple providers (AniList, TMDB) dynamically. We modeled our `ExternalMapping` to similarly capture rich provider specific data (like typing `tmdb_tv` vs `tmdb_movie`) and provenance (`source_revision`, `confidence`), to allow multiple `Work` models to map to a single external TVDB/TMDB identity, avoiding strict 1:1 relationships which break on offset anime seasons.
3. **Immutability of Storage**:
    - Jimaku performs file processing and storage safely. We adopted a `SubtitleBlob` immutable storage system. When operators import `.ass` or `.srt` files, the source is never altered. Instead, a SHA-256 hash is computed, the blob is stored safely using a key derived from this hash, and identical files deduplicate implicitly without losing catalog-level (`SubtitleEntry`) associations.
4. **Pacing and API Handling (AniList vs AniDB)**:
    - Jimaku's `src/anilist.rs` gracefully checks GraphQL rate-limit responses (e.g., `Retry-After`). Since the MVP connects to AniDB, which operates using an HTTP API masquerading XML errors inside HTTP 200 responses, we implemented a custom `AniDBClient` using a shared `AniDBState` database record. This ensures budgets and pacings (e.g., 1 request per 2 seconds) are strictly shared among any possible worker threads/processes, avoiding bans.

## Limitations & Non-Adopted Features

- Code was entirely rewritten in Python/Django; no direct Rust code was copied to avoid immediate entanglements with AGPL obligations until a global project license is decided.
- Features related to public uploads, vectors, or Discord were deliberately skipped to keep the scope tied to the MVP.
