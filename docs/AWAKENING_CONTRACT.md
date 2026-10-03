# Agent-Native Awakening Contract

The historical curator is a dependency-injected, event-driven module; it does not import model vendors, cloud SDKs, IDE globals, or generate executable UI code.

## Event boundary

Every catalog payload is passed through `covenant/sanctuary-gateway.ts`'s `sanitize()` before it reaches `CuratorAgent.curate()`. Sanitization requires a non-empty event ID, title, date, and between one and 100 provenance references; it applies Unicode normalization and field limits, removes control characters, rejects markup-like text, and returns only the allowlisted `HistoricalEvent` fields. Untrusted extra properties are discarded. Missing provenance rejects the event before curation.

Curator results must be structured `CuratorDraft` data with bounded plain-text fields; markup-like summaries are rejected. Provenance must contain at most 100 references, be non-empty, and be drawn from the sanitized event's provenance list. If a result is marked incomplete, its summary must begin with **“record incomplete”**. Events without a source summary must be marked incomplete. Deployed `CuratedComponent` objects contain only typed text and provenance fields; render them as escaped text, never as raw HTML or executable markup.

## Steward accountability

Each event handling attempt first durably appends `CURATION_AUTHORIZED` before deployment can begin; it then appends `CURATION_DEPLOYED` after success or `CURATION_REJECTED` on failure. The injected governance-ledger `append()` must resolve only after its record is durably committed. Records include steward ID, sanitized event ID when available, and timestamp, but not the source event body. The module performs no autonomous writes beyond the injected `RelationalCore.deployComponent()` and governance-ledger interfaces.

## Interfaces and lifecycle

`DataCatalog` mounts a named table and registers an async event listener. `RelationalCore` initializes and accepts only `CuratedComponent`. `CuratorAgent` receives a sanitized `HistoricalEvent` plus an explicitly supplied system prompt. `awakenAgentNativeCore()` mounts and initializes dependencies, subscribes to events, and returns a stop function for unsubscribing. The Python service/ledger adapter is not implemented by this contract.

The Vitest mocks implement these interfaces without cloud or model packages. They expose catalog `mounted` records, relational `initialized`/`deployed` arrays, curator `inspected` events, and async catalog `emit()` for exercising the full flow.
