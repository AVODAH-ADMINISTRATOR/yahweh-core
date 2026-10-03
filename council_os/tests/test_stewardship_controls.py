import json
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


def test_sealing_is_append_only_and_compensation_requires_two_witnesses():
    from council_os.ledger import DualControlApproval

    ledger = LifecycleLedger()
    original = ledger.append(KernelDomain.LEDGER, "ORIGINAL", {"value": "one"})
    seal = ledger.seal(original.index)
    assert seal.event == f"LEDGER_ENTRY_SEALED:{original.index}"
    assert ledger.is_sealed(original.index)
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


def test_ledger_serializes_concurrent_writers(tmp_path: Path):
    import threading

    path = tmp_path / "concurrent-ledger.jsonl"
    ledger = LifecycleLedger(path)
    errors: list[BaseException] = []

    def worker(label: str) -> None:
        try:
            for index in range(20):
                ledger.append(KernelDomain.LEDGER, f"EVT_{label}_{index}", {"n": index})
        except BaseException as exc:  # pragma: no cover - collected below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(name,)) for name in ("a", "b", "c", "d")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(ledger) == 80
    assert ledger.verify_chain()
    restored = LifecycleLedger(path)
    assert restored.verify_chain()
    assert len(restored) == 80


def test_sealed_markers_require_valid_target_identifiers():
    from council_os.ledger import DualControlApproval, parse_seal_target

    ledger = LifecycleLedger()
    original = ledger.append(KernelDomain.LEDGER, "ORIGINAL", {"value": "one"})
    assert parse_seal_target("LEDGER_ENTRY_SEALED:0") == 0
    assert parse_seal_target("LEDGER_ENTRY_SEALED:0x1") is None
    assert parse_seal_target("LEDGER_ENTRY_SEALED:-1") is None

    with pytest.raises(CharterViolation, match="invalid sealed ledger marker"):
        ledger.append(
            KernelDomain.LEDGER,
            "LEDGER_ENTRY_SEALED:00abc",
            {"sealed_index": 0, "sealed_entry_id": original.entry_id},
        )
    with pytest.raises(CharterViolation, match="target"):
        ledger.append(
            KernelDomain.LEDGER,
            "LEDGER_ENTRY_SEALED:0",
            {"sealed_index": 0, "sealed_entry_id": "000000-LDG-1-deadbeefdead"},
        )
    seal = ledger.seal(original.index)
    assert seal.event == "LEDGER_ENTRY_SEALED:0"
    assert ledger.is_sealed(original.index)
    with pytest.raises(CharterViolation, match="already sealed"):
        ledger.seal(original.index)
    compensation = ledger.compensate_sealed(
        original.index,
        KernelDomain.LEDGER,
        "COMPENSATION",
        DualControlApproval("witness-a", "witness-b", "correction"),
    )
    assert compensation.event == "COMPENSATION"
    assert ledger.verify_chain()
