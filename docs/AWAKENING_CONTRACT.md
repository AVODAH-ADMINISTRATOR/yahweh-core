# Agent-Native Awakening Contract

The historical curator is a dependency-injected, event-driven module under `covenant/`; it does not import model vendors, cloud SDKs, IDE globals, or generate executable UI code. Sample or legacy seal modules outside `covenant/` are out of scope for this contract and are not the runtime curator path.

## Event boundary

Every catalog payload is passed through `covenant/sanctuary-gateway.ts`'s `sanitize()` before it reaches `CuratorAgent.curate()`. Sanitization requires a non-empty event ID, title, date, and between one and **32** provenance references; it applies Unicode normalization and per-field length limits, removes control characters, rejects markup-like text, and returns only the allowlisted `HistoricalEvent` fields. Untrusted extra properties are discarded. Missing provenance, oversized provenance lists, or oversized provenance strings reject the event before curation.

Curator results must be structured `CuratorDraft` data with bounded plain-text fields; markup-like summaries are rejected. Provenance must be non-empty, at most 32 references, drawn only from the sanitized event's provenance list, and within the same per-item length limit as catalog input. If a result is marked incomplete, its summary must begin with the exact prefix **record incomplete**. Events without a source summary must be marked incomplete. Deployed `CuratedComponent` objects contain only typed text and provenance fields; render them as escaped text, never as raw HTML or executable markup.

## Steward accountability

Each event handling attempt appends exactly one of `CURATION_DEPLOYED` or `CURATION_REJECTED`, plus steward ID, sanitized event ID when available, and timestamp, through the injected governance-ledger interface. **`CURATION_DEPLOYED` is appended durably before `RelationalCore.deployComponent()` runs**; rejection is recorded when sanitization, curation, or validation fails before that deploy record. The record does not copy the source event body. Concurrent catalog events are serialized through a single write queue so governance and deploy writes do not interleave. The module performs no autonomous writes beyond the injected `RelationalCore.deployComponent()` and governance-ledger interfaces, which must enforce their own authorization and append-only requirements.

## Interfaces and lifecycle

`DataCatalog` mounts a named table and registers an async event listener. `RelationalCore` initializes and accepts only `CuratedComponent`. `CuratorAgent` receives a sanitized `HistoricalEvent` plus an explicitly supplied system prompt. `awakenAgentNativeCore()` mounts and initializes dependencies, subscribes to events, and returns a stop function for unsubscribing.

The durable Python `LifecycleLedger` in `council_os/ledger.py` is a separate append-only hash chain used by the kernel; it serializes concurrent writers, validates sealed markers (`LEDGER_ENTRY_SEALED:<index>`) and target entry identifiers, and is not a drop-in adapter for this TypeScript contract. This contract does not implement a Python service bridge.

The Vitest mocks implement these interfaces without cloud or model packages. They expose catalog `mounted` records, relational `initialized`/`deployed` arrays, curator `inspected` events, and async catalog `emit()` for exercising the full flow.
