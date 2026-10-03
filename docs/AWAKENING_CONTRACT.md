# Agent-Native Awakening Contract

The historical curator is a dependency-injected, event-driven module; it does not import model vendors, cloud SDKs, IDE globals, or generate executable UI code.

## Event boundary

Every catalog payload is passed through `covenant/sanctuary-gateway.ts`'s `sanitize()` before it reaches `CuratorAgent.curate()`. Sanitization requires a valid target identifier, title, date, and 1–100 provenance references (each at most 1,000 characters); it applies Unicode normalization and field limits, removes control characters, rejects markup-like text, and returns only the allowlisted `HistoricalEvent` fields. Untrusted extra properties are discarded. Missing or excessive provenance rejects the event before curation.

Curator results must be structured `CuratorDraft` data with bounded plain-text fields; markup-like summaries are rejected. Output provenance must contain 1–100 references, each bounded and drawn from the sanitized event's provenance list. If a result is marked incomplete, its summary must begin with **“record incomplete”**. Events without a source summary must be marked incomplete. Deployed `CuratedComponent` objects contain only typed text and provenance fields; render them as escaped text, never as raw HTML or executable markup.

## Steward accountability

Each event handling attempt records a validated governance marker, steward ID, target event ID when available, and timestamp through the injected governance-ledger interface. For accepted curation, `CURATION_APPROVED` must be durably appended before `RelationalCore.deployComponent()` is called; the final `CURATION_DEPLOYED` or `CURATION_REJECTED` outcome is then appended. Ledger writes are serialized. `GovernanceLedger.append()` must resolve only after the record is durably committed and must enforce append-only requirements. The record does not copy the source event body. Persistence and authorization remain the responsibility of the injected interfaces; this module does not implement a storage adapter.

## Interfaces and lifecycle

`DataCatalog` mounts a named table and registers an async event listener. `RelationalCore` initializes and accepts only `CuratedComponent`. `CuratorAgent` receives a sanitized `HistoricalEvent` plus an explicitly supplied system prompt. `awakenAgentNativeCore()` mounts and initializes dependencies, subscribes to events, and returns a stop function for unsubscribing. This contract covers the dependency-injected curator flow only; the Python service/ledger adapter is not implemented here.

The Vitest mocks implement these interfaces without cloud or model packages. They expose catalog `mounted` records, relational `initialized`/`deployed` arrays, curator `inspected` events, and async catalog `emit()` for exercising the full flow.
