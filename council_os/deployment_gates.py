"""Deployment Gate Verification Module.

Enforces pre-flight checks and sealed ledger validation before kernel
state transitions, job scheduling, or mesh synchronization operations.
"""

from __future__ import annotations

from typing import Optional

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.ledger import LifecycleLedger


def verify_deployment_gate(ledger: LifecycleLedger, required_seal_index: Optional[int] = None) -> bool:
    """Validate ledger chain integrity and optional entry sealing."""
    if not ledger.verify_chain():
        raise CharterViolation("Deployment Gate Blocked: Ledger chain integrity failed")
    if required_seal_index is not None and not ledger.is_sealed(required_seal_index):
        raise CharterViolation(f"Deployment Gate Blocked: Entry at index {required_seal_index} is not sealed")
    ledger.append(
        KernelDomain.GOVERNANCE,
        "DEPLOYMENT_GATE_VERIFIED",
        {"entries_checked": len(ledger.entries), "chain_valid": True},
    )
    return True


def gate_state_transition(ledger: LifecycleLedger, transition_type: str, target_domain: str) -> None:
    """Pre-flight guard for kernel state transitions."""
    verify_deployment_gate(ledger)
    ledger.append(
        KernelDomain.GOVERNANCE,
        f"STATE_TRANSITION_GATED:{transition_type}",
        {"target_domain": target_domain, "gate_result": "PASS"},
    )
