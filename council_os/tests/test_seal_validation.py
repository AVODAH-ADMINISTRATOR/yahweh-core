from dataclasses import replace

import pytest

from council_os.business import BusinessGovernance
from council_os.domains import KernelDomain
from council_os.kernel import CouncilOSKernel
from council_os.manifests import (
    BootSeal,
    ManifestRegistry,
    SealValidationError,
    seal_ledger_record,
    validate_identifier,
    validate_sealed_marker,
    verify_sealed_ledger_record,
)


VALID_MARKER = "a" * 64


@pytest.mark.parametrize("marker", [VALID_MARKER, "0123456789abcdef" * 4])
def test_validate_sealed_marker_accepts_sha256_hex(marker: str):
    validate_sealed_marker(marker)


@pytest.mark.parametrize(
    "marker",
    [None, 1, *("a" * length for length in range(64)), "a" * 65, "A" * 64, "g" * 64],
)
def test_validate_sealed_marker_rejects_invalid_values(marker):
    with pytest.raises(SealValidationError):
        validate_sealed_marker(marker)


@pytest.mark.parametrize("identifier", ["node-01", "ledger_entry.2", "A_1", "x" * 256])
def test_validate_identifier_accepts_allowed_values(identifier: str):
    validate_identifier(identifier)


@pytest.mark.parametrize(
    "identifier",
    [None, 1, "", "x" * 257, "../secret", "name/path", "name\\path", "has space"],
)
def test_validate_identifier_rejects_invalid_values(identifier):
    with pytest.raises(SealValidationError):
        validate_identifier(identifier)


def test_manifest_signing_rejects_invalid_identifiers():
    registry = ManifestRegistry(b"test signing key", CouncilOSKernel().ledger)
    with pytest.raises(SealValidationError):
        registry.sign("scout", "../node", KernelDomain.SCOUT_EDGE, {})

    manifest = registry.sign("scout", "node-01", KernelDomain.SCOUT_EDGE, {})
    manifest.node_id = "../node"
    assert not registry.verify(manifest)


def test_boot_seal_rejects_malformed_markers():
    registry = ManifestRegistry(b"test signing key", CouncilOSKernel().ledger)
    seal = registry.seal_boot({"boot": "ok"})
    assert not registry.verify_boot_seal({"boot": "ok"}, BootSeal("short", seal.signature))
    assert not registry.verify_boot_seal({"boot": "ok"}, replace(seal, signature="A" * 64))


def test_sealed_record_hmac_detects_tampering():
    key = b"test signing key"
    record = seal_ledger_record(VALID_MARKER, "ledger-01", {"event": "sealed"}, key)
    assert verify_sealed_ledger_record(record, key)
    repeated = seal_ledger_record(VALID_MARKER, "ledger-01", {"event": "sealed"}, key)
    assert repeated["integrity_hash"] == record["integrity_hash"]

    tampered = {**record, "data": {"event": "changed"}}
    assert not verify_sealed_ledger_record(tampered, key)
    assert not verify_sealed_ledger_record(record, b"different key")


def test_business_motion_actor_id_is_validated_before_ledger_write():
    board = BusinessGovernance(CouncilOSKernel())
    board.open()
    with pytest.raises(SealValidationError):
        board.propose("operations", "../operator", "approved maintenance")

    assert not any(entry.event == "BUSINESS_MOTION" for entry in board.kernel.ledger.entries)
