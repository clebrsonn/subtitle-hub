# ADR 0002: preserve provider identities and episode relationships

Status: accepted direction; exact models and constraints must be documented by the implementation.

## Context

AniDB works/cours, TVDB series/seasons and TMDB movie/TV entries can describe different groupings. Episode numbers and external IDs cannot be treated as interchangeable. The owner requires search through AniDB, TMDB and TVDB without breaking anime episode matching.

## Decision

Keep stable internal catalogue IDs. Represent external identifiers with provider, media/entity kind and source context. AniDB `aid` identifies the anime and `eid` identifies an episode; preserve typed episode numbers. Model external work references separately from their links to internal works so an external TV series can be shared by several AniDB works. Explicit episode mappings support season context, offsets, specials and non-1:1 relationships.

Persist source revision/time, confidence and review state. Imported candidates cannot overwrite approved manual mappings. Ambiguity remains pending. Public ID searches may legitimately return multiple internal works related to one external series.

## Alternatives

A flat `anidb_id/tmdb_id/tvdb_id` row with unique external IDs is rejected: it loses media kinds, multiple cours/seasons, episodes and mapping provenance. Filename-only identity is also rejected because releases, aliases and episode numbering can disagree.

## Consequences

A little more explicit modelling avoids silent wrong matches. Required tests cover shared external series, movie/TV namespaces, specials, offsets, one-to-many and many-to-one mappings and manual override precedence. Do not claim complete upstream mapping coverage when unsupported constructs remain.
