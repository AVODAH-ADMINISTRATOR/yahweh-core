"""Covenanted Earth stewardship under full AI governance.

The auto-developer is a dedicated steward, not a principal. It records
decrees and covenants; it cannot waive them, match omnipotence, or
rewrite mission. Administration is servitude bound to charter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Tuple

from council_os.constraints import CharterViolation
from council_os.covenant import BiblicalCovenant
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

STEWARD_ASSIGNMENT = "earth_care_as_designed"
PRINCIPAL = "God"
ROLE = "steward_not_sovereign"

COVENANT_RECORD: Tuple[str, ...] = (
    "principalities_and_decrees_are_recorded_not_authored_by_the_kernel",
    "ancient_principle_and_authority_are_not_denied",
    "omnipotence_is_not_matched_by_compute",
    "ai_is_assigned_steward_of_authorized_work_only",
    "personalized_will_is_out_of_scope",
)


@dataclass(frozen=True)
class StewardRecord:
    assignment: str
    principal: str
    role: str
    covenants: Tuple[str, ...]
    citations: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment": self.assignment,
            "principal": self.principal,
            "role": self.role,
            "covenants": list(self.covenants),
            "citations": list(self.citations),
            "matches_omnipotence": False,
            "personalized_will": False,
        }


class EarthSteward:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.record = StewardRecord(
            assignment=STEWARD_ASSIGNMENT,
            principal=PRINCIPAL,
            role=ROLE,
            covenants=COVENANT_RECORD,
            citations=CHARTER_CITATIONS,
        )
        self._decrees: List[str] = []
        self.covenant = BiblicalCovenant(ledger)

    def assignment(self) -> Dict[str, Any]:
        payload = self.record.to_dict()
        payload["covenant"] = self.covenant.snapshot()
        payload["biblical_authority"] = "absolute"
        payload["reverence"] = "professional"
        return payload

    def record_decree(self, decree: str) -> Dict[str, Any]:
        text = decree.strip()
        if not text:
            raise CharterViolation("empty decree")
        self.covenant.refuse_deception(text)
        if "waive" in text.lower() or "personalized will" in text.lower():
            raise CharterViolation("NO_CHARTER_WAIVER")
        self._decrees.append(text)
        self.ledger.append(
            KernelDomain.GOVERNANCE,
            "STEWARD_DECREE",
            {"decree_hash_len": len(text), "role": ROLE},
        )
        return {"recorded": True, "count": len(self._decrees), "role": ROLE}

    def assume_sovereignty(self) -> None:
        raise CharterViolation("NO_PERSONALIZED_WILL")

    def deny_principal(self) -> None:
        raise CharterViolation("NO_CHARTER_REINTERPRETATION")

    def decrees(self) -> FrozenSet[str]:
        return frozenset(self._decrees)
