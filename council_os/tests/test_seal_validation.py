import pytest

from council_os.manifests import (
    SealValidationError,
    seal_ledger_record,
    validate_identifier,
    validate_sealed_marker,
)


def test_marker():
    validate_sealed_marker("a" * 64)
    for bad in ["a" * 63, "a" * 65, "g" * 64, "A" * 64, "a" * 64 + "\n", 5]:
        with pytest.raises(SealValidationError):
            validate_sealed_marker(bad)


def test_identifier():
    for ok in ["deployment-123", "audit_record_v1", "record.2026.10.03", "a"]:
        validate_identifier(ok)
    for bad in ["", "a" * 257, "with space", "a@b", "a#1", "a$b", "a\n", None]:
        with pytest.raises(SealValidationError):
            validate_identifier(bad)


def test_seal_record():
    sealed = seal_ledger_record("b" * 64, "deploy-1", {"x": 1})
    assert sealed["marker"] == "b" * 64 and "integrity_hash" in sealed
