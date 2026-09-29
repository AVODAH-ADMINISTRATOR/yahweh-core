"""Dedicated intel gathering for developer workflows.

Collects scientifically measured facts about a job: citations, domain,
constraints, and quality signals. This is analysis of authorized work,
not host scanning or credential capture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

FORBIDDEN_INTEL = frozenset(
    {"passphrase", "password", "wifi_key", "mac_harvest", "credential_capture"}
)


@dataclass
class IntelBrief:
    workflow_id: str
    domain: str
    observations: List[str]
    citations: List[str]
    measurements: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "domain": self.domain,
            "observations": list(self.observations),
            "citations": list(self.citations),
            "measurements": dict(self.measurements),
        }


class IntelDesk:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.briefs: Dict[str, IntelBrief] = {}

    def gather(
        self,
        workflow_id: str,
        domain: KernelDomain,
        observations: Optional[List[str]] = None,
        measurements: Optional[Dict[str, float]] = None,
    ) -> IntelBrief:
        notes = observations or []
        lowered = " ".join(notes).lower()
        if any(token in lowered for token in FORBIDDEN_INTEL):
            raise CharterViolation("intel desk refuses credential capture")
        brief = IntelBrief(
            workflow_id=workflow_id,
            domain=domain.value,
            observations=notes,
            citations=list(CHARTER_CITATIONS),
            measurements=dict(measurements or {}),
        )
        self.briefs[workflow_id] = brief
        self.ledger.append(
            KernelDomain.SCOUT_EDGE,
            "INTEL_BRIEF",
            {
                "workflow_id": workflow_id,
                "domain": domain.value,
                "observation_count": len(notes),
            },
        )
        return brief
