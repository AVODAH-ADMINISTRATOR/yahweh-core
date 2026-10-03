import pytest

from council_os.manifests import (
    IDENTIFIER_MAX_LENGTH,
    SealValidationError,
    seal_ledger_record,
    validate_identifier,
    validate_sealed_marker,
)


@pytest.mark.parametrize("m", ["A" * 64, "a" * 63, "a" * 65, "g" * 64, 12345, None, "a" * 64 + "\n"])
def test_bad_markers(m):
    with pytest.raises(SealValidationError):
        validate_sealed_marker(m)


@pytest.mark.parametrize("i", ["", "a" * (IDENTIFIER_MAX_LENGTH + 1), "a b", "a@b", "a/b", "a\\b", "a\n", 5, ["x"]])
def test_bad_identifiers(i):
    with pytest.raises(SealValidationError):
        validate_identifier(i)


def test_valid_and_seal():
    validate_sealed_marker("a" * 64)
    for i in ["a", "deployment-123", "record.2026.10.03", "PROD_SEAL"]:
        validate_identifier(i)
    s1 = seal_ledger_record("b" * 64, "id-1", {"k": 1})
    s2 = seal_ledger_record("b" * 64, "id-1", {"k": 1})
    assert s1["integrity_hash"] == s2["integrity_hash"] and len(s1["integrity_hash"]) == 64
    with pytest.raises(SealValidationError):
        seal_ledger_record("bad", "id", {})
    with pytest.raises(SealValidationError):
        seal_ledger_record("b" * 64, "bad id", {})
