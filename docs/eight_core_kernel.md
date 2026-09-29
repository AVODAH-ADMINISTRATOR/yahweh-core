# Eight-Domain Council OS Kernel

Council OS remains a virtualized kernel, decoupled from host hardware. The former four quadrants are expressed as eight governed domains. Capability is doubled by splitting load across service boundaries, not by granting autonomy or personalized will.

## Domains

| Domain | Port | Origin quadrant | GPU |
| --- | --- | --- | --- |
| identity | 8101 | identity/ledger | no |
| ledger | 8102 | identity/ledger | no |
| linguistic_nlp | 8103 | communal / scholarly | translation training only (8-GPU profile) |
| textual_criticism | 8104 | communal / scholarly | no |
| scout_edge | 8105 | alliance bridge | no |
| governance | 8106 | operations/runtime | no |
| treasury | 8107 | operations/runtime | no |
| sentinel | 8108 | operations/runtime | no |

Each domain has independent health, append-only logs, rollback snapshots, and a kill switch. The mesh is scheduled and auditable. Unattended work requires human authorization.

## Compile-time policy

`python -m council_os.policy` binds `docs/linguistic_theological_charter.md` and `docs/ethical_ai_governance.md` before merge or deploy. AI may propose parses, variants, and alignments. It must not commit authoritative text, funds, or policy. Self-modifying production code, hidden reward loops, and mission-rewrite endpoints fail the charter gate.

## Subordinate network

Scout, gateway, and core nodes sync only through HMAC-SHA256 manifests plus human approval. Sealed ledger entries cannot be rewritten; dual control may append a compensating record. AI value memory is forbidden.

## Fidelity

Devotion is scored as fidelity: charter citations, intact constraints, cryptographic audit chain, scholar HITL, PII redaction, and refusal to harm. Compassion is those operational controls, not simulated emotion.
