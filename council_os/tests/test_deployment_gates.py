import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation
from council_os.deployment_gates import gate_state_transition, verify_deployment_gate
from council_os.domains import KernelDomain
from council_os.ledger import LifecycleLedger


def _ledger():
    ledger = LifecycleLedger()
    ledger.append(KernelDomain.GOVERNANCE, "BOOT", {})
    return ledger


def test_chain_integrity_detects_corruption():
    ledger = _ledger()
    ledger.entries[0].entry_hash = "bad"
    with pytest.raises(CharterViolation):
        verify_deployment_gate(ledger)


def test_unsealed_entry_rejected_and_sealed_accepted():
    ledger = _ledger()
    with pytest.raises(CharterViolation):
        verify_deployment_gate(ledger, required_seal_index=0)
    ledger.seal(0)
    assert verify_deployment_gate(ledger, required_seal_index=0) is True


def test_gate_logs_verification_event():
    ledger = _ledger()
    verify_deployment_gate(ledger)
    assert ledger.entries[-1].event == "DEPLOYMENT_GATE_VERIFIED"


def test_state_transition_logged():
    ledger = _ledger()
    gate_state_transition(ledger, "SCHEDULE", "governance")
    assert ledger.entries[-1].event == "STATE_TRANSITION_GATED:SCHEDULE"


def test_state_transition_blocked_on_corruption():
    ledger = _ledger()
    ledger.entries[0].entry_hash = "bad"
    with pytest.raises(CharterViolation):
        gate_state_transition(ledger, "RELEASE", "fidelity")
