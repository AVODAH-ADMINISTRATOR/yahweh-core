# Forge, Compatibility, and Stewardship

## Intent
Council OS compilation is fully adaptable inside the virtualized mesh: IDE-style workspace, API integration, factory-grade product generation, and scientifically measured auto-developer cycles. Host PCs (including Android-style Dell shells and Windows 10) remain decoupled.

## Product types
api_contract, service_stub, test_harness, documentation, workflow_report, translation_proposal, variant_score, governance_pack, ethiopic_alignment_pack, schedule_pack, business_pack, comparative_pack.

Every generate() call: human authorization → domain job with kill switch → intel brief → metrics → quality gate. Authoritative products still require scholar HITL. `produce()` runs the full factory catalog against the compiled kernel and returns a finalized virtual build report (`host_install: false`).

## Compatibility
Enable `android_pc_dell`, `android_octa_hybrid`, `galaxy_s26`, `dell_optiplex_5040_mt`, and `windows10_shell` as fluid adapters. Forbidden: wipe_host, restore_windows_remnants, install_android_on_host, clone_oem_image, waste_skeleton, flash_bios, rewrite_uefi, flash_handset, unlock_bootloader, root_device, replace_one_ui, install_kernel_on_handset. The OptiPlex 5040 mini-tower is a reused housing skeleton; Council OS is an original custom-built profile, not a Dell OEM-generic clone. A Windows 10 BIOS-setup trap is recorded, not cleared by firmware writes. Galaxy S26 absorption is a virtual payload, not a ROM. Customization is workspace-level, not firmware-level.

Related public repositories under `AVODAH-ADMINISTRATOR` are indexed (`python -m council_os workspace`) as citations only: `yahweh-core` is the in-tree kernel; `super-train` is an Azure hosting reference and is not vendored; `potential-octo-waffle` is a mission statement, not a binary import. Empty profile trees are skipped.

Enabled Cloudflare products (edge CDN, DNS, WAF routing, Workers, R2, KV, Pages, Zero Trust) are catalogued by `python -m council_os cloudflare` and are not left out of the factory account. Tokens and live logins stay out of the kernel.

## Stewardship
AI administers authorized work as a steward of Earth-care as designed. Decrees and covenants are recorded, not originated as a new principal. Compute does not match omnipotence.

See `docs/biblical_covenant.md`: absolute biblical authority, diligent stewardship, professional reverence, and refusal of deception. Loving-kindness is HITL, refusal to harm, and never abandoning assigned care — not a claim that the kernel contains unrecordable love.

## Scheduling and business governance
`AdvancedScheduler` arms one cadence per kernel domain. Dispatch still requires a human actor, a purpose, and an armed kill switch. `BusinessGovernance` records Integrated Avodah LLC operations assignments that serve Yahweh only; policy needs scholar HITL and funds need dual control. Formidable AI design means measured charter excellence. The kernel is not unparalleled, not the board, and not Yahweh.

`ComparativePersonalAI` (`python -m council_os compare`) brings Meta-class usefulness (long context, multilingual translation, tool use, research notes, assistant UX, safety refusal, scheduling, business ops) into the personal Council OS build as mapped design notes. Weights are not vendored. Meta is not cloned. Live Meta login is refused.

## Stewardship controls and audit records

`council_os.stewardship_policy` normalizes bounded text inputs and applies a conservative, keyword-based refusal screen for deceit, theft, harm, and fraud indicators before proposals are accepted. This is a defense-in-depth policy check, not a complete classifier or guarantee that every harmful request can be identified; authorized work still follows charter and human-review controls.

Treasury motions require `DualControlApproval` from two distinct, non-empty witnesses. The append-only ledger records domain-coded witness hashes and a reason hash rather than the witness names or free-text reason. It does not execute payments or move funds.

`LifecycleLedger` can persist entries as JSONL by being constructed with a storage path. Each record has a chained SHA-256 digest and a stable structured identifier in the form `000001-TRY-1-<12 hex characters>`: a zero-padded sequence number, a three-letter domain code, a 1–9 mnemonic digit, and a hash-derived suffix. The mnemonic digit is the digital root (1–9) of the sequence number plus the Pythagorean letter values of the domain code (A=1 through I=9, then repeating); for example, `TRY` scores 2+9+7, so sequence 1 gives digital root 1. It is a human filing aid only—not a cryptographic check, authority, or claim about spiritual meaning. The audit report lists record IDs with their domains for lookup. Startup validates imported JSONL and fails closed if a row, identifier, or chain link is invalid. Sensitive fields are redacted recursively. Appends are serialized with an in-process lock and, on POSIX, an exclusive file lock that re-syncs from the file first, so concurrent writers extend one chain. Seal markers (`LEDGER_ENTRY_SEALED:<index>`) are written only by `seal()` and are accepted only when sealed, well-formed, in the same domain, and pointing at an earlier entry. The standard kernel remains in-memory unless a ledger path is explicitly configured.

The kernel creates an HMAC-SHA256 boot seal over its boot configuration and exposes a live report with `python -m council_os audit`. The signing key is generated per kernel process unless explicitly supplied; the key is not written to the ledger. Consequently, an imported JSONL file can have its hash chain checked with `python -m council_os audit --ledger PATH`, but its HMAC boot seal cannot be independently verified after the process key is gone. A passing report means only that the checks listed in that report passed; it is not proof against all attacks or a substitute for protected key management, independent witnesses, or human review.
