import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.kernel import CouncilOSKernel
from council_os.ledger import LifecycleLedger
from council_os.manifests import ManifestRegistry
from council_os.stewardship_policy import check_action_policy, sanitize_text


def test_pythagorean_record_digit_uses_repeating_letter_values():
    assert [LifecycleLedger.numerology_digit(1, code) for code in ("IDN", "LDG", "LNG", "TXT", "EDG", "GOV", "TRY", "SNT")] == [1, 6, 7, 2, 8, 9, 1, 9]
    assert LifecycleLedger.numerology_digit(2, "TRY") == 2


def test_action_policy_blocks_deceit_theft_harm_and_fraud():
    for phrase, category in (
        ("deceive the reviewer", "deceit"),
        ("steal restricted funds", "theft"),
        ("harm a person", "harm"),
        ("commit fraud", "fraud"),
    ):
        with pytest.raises(CharterViolation, match=category):
            check_action_policy("propose", {"intent": phrase})
    check_action_policy("document", {"intent": "record approved maintenance"})
    check_action_policy("document", {"intent": "forgive an error"})


def test_input_sanitization_normalizes_and_bounds_text():
    assert sanitize_text("  cafe\u0301\x00  ") == "café"
    with pytest.raises(CharterViolation, match="must not be empty"):
        sanitize_text("\x00\t ")
    with pytest.raises(CharterViolation, match="maximum length"):
        sanitize_text("long", max_length=3)


def test_jsonl_ledger_persists_hashed_domain_ids_and_detects_tampering(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = LifecycleLedger(path)
    entry = ledger.append(
        KernelDomain.TREASURY,
        "TEST_EVENT",
        {"nested": [{"api_key": "do-not-store"}], "ok": True},
    )
    assert entry.entry_id.startswith("000001-TRY-1-")
    assert len(entry.entry_id.rsplit("-", 1)[1]) == 12
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["payload_hash"] == entry.payload_hash
    assert "do-not-store" not in path.read_text(encoding="utf-8")
    restored = LifecycleLedger(path)
    assert restored.verify_chain()
    assert restored.entries[0].entry_id == entry.entry_id

    row["event"] = "TAMPERED"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(CharterViolation, match="integrity verification failed"):
        LifecycleLedger(path)


def test_persistent_ledger_serializes_writers_and_refreshes_stale_instances(tmp_path: Path):
    path = tmp_path / "concurrent-ledger.jsonl"
    ledgers = [LifecycleLedger(path), LifecycleLedger(path)]

    def append_entry(sequence: int):
        return ledgers[sequence % 2].append(
            KernelDomain.LEDGER,
            f"CONCURRENT_{sequence}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        entries = list(executor.map(append_entry, range(32)))

    restored = LifecycleLedger(path)
    assert len(entries) == 32
    assert sorted(entry.index for entry in entries) == list(range(32))
    assert len(restored) == 32
    assert restored.verify_chain()
    assert len({entry.entry_hash for entry in restored.entries}) == 32


def test_boot_seal_and_audit_report_detect_tampering():
    kernel = CouncilOSKernel(signing_key=b"test signing key")
    kernel.compile()
    assert kernel.audit_report()["status"] == "passed"
    kernel.boot_payload["virtualized"] = False
    report = kernel.audit_report()
    assert report["status"] == "failed"
    assert report["checks"]["hmac_boot_seal"] is False


def test_manifest_boot_seal_is_bound_to_key_and_body():
    ledger = LifecycleLedger()
    first = ManifestRegistry(b"first key", ledger)
    second = ManifestRegistry(b"second key", ledger)
    body = {"boot": "ok"}
    seal = first.seal_boot(body)
    assert first.verify_boot_seal(body, seal)
    assert not second.verify_boot_seal(body, seal)
    assert not first.verify_boot_seal({"boot": "changed"}, seal)


def test_treasury_approval_records_two_distinct_hashed_witnesses():
    from council_os.forge import AutoDeveloperForge
    from council_os.ledger import DualControlApproval, sha256_hex

    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    motion = forge.business.propose("funds", "treasurer", "Stewardship allocation")
    forge.business.ratify(
        motion["motion_id"],
        dual=DualControlApproval("witness-a", "witness-b", "approved"),
    )
    event = next(entry for entry in kernel.ledger.entries if entry.event == "DUAL_WITNESS_APPROVAL")
    assert event.payload_hash
    assert sha256_hex("witness-a") != sha256_hex("witness-b")
    assert kernel.ledger.verify_chain()


def test_sealing_is_append_only_and_compensation_requires_two_witnesses(tmp_path: Path):
    from council_os.ledger import DualControlApproval

    ledger = LifecycleLedger(tmp_path / "sealed-ledger.jsonl")
    original = ledger.append(KernelDomain.LEDGER, "ORIGINAL", {"value": "one"})
    with pytest.raises(CharterViolation, match="seal markers must be created with seal"):
        ledger.append(KernelDomain.LEDGER, f"LEDGER_ENTRY_SEALED:{original.index}")
    assert not ledger.is_sealed(original.index)

    seal = ledger.seal(original.index)
    assert seal.event == f"LEDGER_ENTRY_SEALED:{original.index}"
    assert seal.seal_target_index == original.index
    assert seal.seal_target_id == original.entry_id
    assert ledger.is_sealed(original.index)
    assert LifecycleLedger(ledger.storage_path).is_sealed(original.index)
    seal.seal_target_id = "forged-target-id"
    assert not ledger.is_sealed(original.index)
    seal.seal_target_id = original.entry_id
    compensation = ledger.compensate_sealed(
        original.index,
        KernelDomain.LEDGER,
        "COMPENSATION",
        DualControlApproval("witness-a", "witness-b", "correction"),
    )
    assert compensation.event == "COMPENSATION"
    assert ledger.verify_chain()


def test_scheduled_actions_are_screened_before_dispatch():
    kernel = CouncilOSKernel()
    kernel.compile()
    with pytest.raises(CharterViolation, match="stewardship policy refused deceit"):
        kernel.schedule(
            KernelDomain.GOVERNANCE,
            "deceive_reviewer",
            "operator",
            "approved task",
        )


def test_kernel_can_use_a_persistent_jsonl_ledger(tmp_path: Path):
    path = tmp_path / "kernel-ledger.jsonl"
    kernel = CouncilOSKernel(signing_key=b"test key", ledger_path=path)
    kernel.compile()
    restored = LifecycleLedger(path)
    assert restored.verify_chain()
    assert len(restored) == len(kernel.ledger)
    assert any(entry.event == "KERNEL_BOOT" for entry in restored.entries)
