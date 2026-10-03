# Agent-Native Awakening Contract

The historical curator is a dependency-injected, event-driven module; it does not import model vendors, cloud SDKs, IDE globals, or generate executable UI code.

## Event boundary

Every catalog payload is passed through `covenant/sanctuary-gateway.ts`'s `sanitize()` before it reaches `CuratorAgent.curate()`. Sanitization requires a non-empty event ID, title, date, and at least one provenance reference; it applies Unicode normalization and field limits, removes control characters, rejects markup-like text, and returns only the allowlisted `HistoricalEvent` fields. Provenance is limited to 32 references and 8,192 total characters, in addition to the 1,000-character per-reference limit. Untrusted extra properties are discarded. Missing or oversized provenance rejects the event before curation.

Curator results must be structured `CuratorDraft` data with bounded plain-text fields; markup-like summaries are rejected. Provenance must be non-empty, contain no more than 32 references or 8,192 total characters, and be drawn from the sanitized event's provenance list. If a result is marked incomplete, its summary must begin with **“record incomplete”**. Events without a source summary must be marked incomplete. Deployed `CuratedComponent` objects contain only typed text and provenance fields; render them as escaped text, never as raw HTML or executable markup.

## Steward accountability

Rejected events append `CURATION_REJECTED`. Validated events first append a durable `CURATION_PENDING` intent; deployment occurs only after that append succeeds, followed by `CURATION_DEPLOYED` or `CURATION_REJECTED`. The records contain steward ID, sanitized event ID when available, and timestamp, but do not copy the source event body. `RelationalCore.deployComponent()` implementations must be idempotent by component `eventId`, so a retry after an interrupted deployment does not create a duplicate. The module performs no autonomous writes beyond the injected deployment and governance-ledger interfaces, which must enforce their own authorization and append-only requirements.

## Interfaces and lifecycle

`DataCatalog` mounts a named table and registers an async event listener. `RelationalCore` initializes and accepts only `CuratedComponent`. `CuratorAgent` receives a sanitized `HistoricalEvent` plus an explicitly supplied system prompt. `awakenAgentNativeCore()` mounts and initializes dependencies, subscribes to events, and returns a stop function for unsubscribing. The Python service/ledger adapter is not implemented by this contract.

The Vitest mocks implement these interfaces without cloud or model packages. They expose catalog `mounted` records, relational `initialized`/`deployed` arrays, curator `inspected` events, and async catalog `emit()` for exercising the full flow.
