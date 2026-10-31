# ADR 0001: a small Django monolith

Status: accepted direction for the implementation proposal.

## Context

The initial product is a subtitle catalogue populated from an owner-prepared directory, with a staff review interface, search and downloads. Avoid creating an infrastructure project before the import and matching behavior is proven.

## Decision

Use Django with server-rendered templates and a PostgreSQL database. Provide management commands for imports and controlled enrichment; keep them in the same codebase. Use a separate managed subtitle-file volume. Select and pin supported dependency versions during implementation.

## Alternatives

- Separate SPA/API plus distributed workers: more deployment and API surface than the MVP needs.
- Fork Jimaku: potentially useful, but introduces a different Rust architecture and a direct-reuse/license decision not approved as part of this implementation. Study the complete upstream as a reference instead.
- SQLite-only acceptance: simpler locally, but would not exercise the selected database and shared pacing/concurrency guarantees.

## Consequences

A small deployable application with straightforward administration. Long imports/enrichment must not run in ordinary public requests. Add a queue only after measured requirements justify it. Public repository visibility does not settle the software/data license or authorize production deployment.
