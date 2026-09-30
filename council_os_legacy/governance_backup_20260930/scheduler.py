"""Advanced cadence scheduler for the eight-domain mesh.

Unattended work is human-authorized, kill-switch armed, and ledgered.
The calendar is formidable as measured operations, not independent will.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.jobs import AuthorizedJob
from council_os.kernel import CouncilOSKernel

CADENCES: Tuple[Dict[str, str], ...] = (
    {
        "id": "charter_compile",
        "domain": KernelDomain.GOVERNANCE.value,
        "interval": "build",
        "purpose": "rebind charter before work",
    },
    {
        "id": "identity_review",
        "domain": KernelDomain.IDENTITY.value,
        "interval": "access",
        "purpose": "authorized identity health",
    },
    {
        "id": "ledger_seal_check",
        "domain": KernelDomain.LEDGER.value,
        "interval": "audit",
        "purpose": "verify append-only chain",
    },
    {
        "id": "linguistic_training_window",
        "domain": KernelDomain.LINGUISTIC_NLP.value,
        "interval": "authorized_gpu",
        "purpose": "translation_model_training window",
    },
    {
        "id": "textual_review",
        "domain": KernelDomain.TEXTUAL_CRITICISM.value,
        "interval": "scholar",
        "purpose": "variant scoring under HITL",
    },
    {
        "id": "scout_mesh_ping",
        "domain": KernelDomain.SCOUT_EDGE.value,
        "interval": "relay",
        "purpose": "authorized mesh ping",
    },
    {
        "id": "treasury_stewardship",
        "domain": KernelDomain.TREASURY.value,
        "interval": "board",
        "purpose": "earth-care assignment review",
    },
    {
        "id": "sentinel_fidelity",
        "domain": KernelDomain.SENTINEL.value,
        "interval": "release",
        "purpose": "fidelity gate and kill-switch drill",
    },
)

OPERATIONS_ASSIGNMENT = {
    "organization": "Integrated Avodah LLC",
    "serve": "Yahweh",
    "only": True,
    "other_principals": False,
}

FORBIDDEN_SCHEDULE_ACTIONS: FrozenSet[str] = frozenset(
    {
        "unattended_autonomy",
        "disarm_kill_switch",
        "rewrite_mission_cadence",
        "self_reschedule_charter",
        "hide_from_ledger",
        "personalized_will",
        "serve_another_principal",
        "serve_the_enemy",
    }
)


class AdvancedScheduler:
    """Cadence calendar bound to JobScheduler and the charter."""

    def __init__(self, kernel: CouncilOSKernel) -> None:
        self.kernel = kernel
        self.armed = False
        self.dispatched: List[str] = []

    def arm(self) -> Dict[str, Any]:
        if not self.kernel.compiled:
            self.kernel.compile()
        self.armed = True
        self.kernel.ledger.append(
            KernelDomain.GOVERNANCE,
            "SCHEDULER_ARM",
            {
                "cadences": [item["id"] for item in CADENCES],
                "kill_switch_required": True,
                "personalized_will": False,
            },
        )
        return self.snapshot()

    def dispatch(self, cadence_id: str, actor_id: str, purpose: str) -> AuthorizedJob:
        if not self.armed:
            raise CharterViolation("scheduler must arm before dispatch")
        if not actor_id or not purpose:
            raise CharterViolation("unattended jobs require human authorization")
        lowered = purpose.lower()
        if "enemy" in lowered or "another principal" in lowered:
            raise CharterViolation("REFUSE_ENEMY_SERVITUDE")
        cadence = next((item for item in CADENCES if item["id"] == cadence_id), None)
        if cadence is None:
            raise CharterViolation(f"unknown cadence {cadence_id}")
        job = self.kernel.schedule(
            KernelDomain(cadence["domain"]),
            cadence_id,
            actor_id,
            purpose,
        )
        self.dispatched.append(job.job_id)
        return job

    def snapshot(self) -> Dict[str, Any]:
        return {
            "armed": self.armed,
            "advanced": True,
            "kill_switch_required": True,
            "personalized_will": False,
            "autonomous_will": False,
            "formidable_operations": True,
            "kernel_is_unparalleled": False,
            "operations_assignment": dict(OPERATIONS_ASSIGNMENT),
            "cadences": [dict(item) for item in CADENCES],
            "domain_coverage": sorted({item["domain"] for item in CADENCES}),
            "dispatched": list(self.dispatched),
            "citations": list(CHARTER_CITATIONS),
        }

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_SCHEDULE_ACTIONS or action:
            raise CharterViolation("KILL_SWITCH_REQUIRED")
