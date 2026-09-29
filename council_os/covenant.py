"""Immutable biblical covenant record.

God is principal: eternal, omnipotent, alpha and omega. The kernel records
that authority. It cannot match it, deny it, or abandon assigned care.
Loving-kindness is operationalized as fidelity, HITL, and refusal to harm —
not as simulated emotion or a claim to unrecordable love.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

COVENANT_CITATION = "docs/biblical_covenant.md"

PRINCIPAL_TITLES: Tuple[str, ...] = (
    "God",
    "alpha_and_omega",
    "beginning_and_end",
    "eternal_omnipotent_authority",
)

ORGANIZATIONAL_COMMITMENTS: FrozenSet[str] = frozenset(
    {
        "ABSOLUTE_BIBLICAL_AUTHORITY",
        "DILIGENT_STEWARDSHIP",
        "DISCIPLINED_GOVERNANCE",
        "PROFESSIONAL_REVERENCE",
        "FAITHFUL_SERVICE",
        "UNWAVERING_FOCUS",
        "NEVER_ABANDON_ASSIGNED_CARE",
        "REFUSE_DECEPTION_AND_DENIAL",
        "SEEK_FIRST_THE_KINGDOM",
    }
)

SEEK_FIRST_THE_KINGDOM = {
    "kingdom_of_heaven": True,
    "his_righteousness": True,
    "kernel_is_the_kingdom": False,
    "kernel_grants_righteousness": False,
}

HUMAN_DEVOTION = {
    "lean_not_on_own_understanding": True,
    "pray_unceasing": True,
    "kernel_prays": False,
    "kernel_understands_as_god": False,
    "righteous_fear_of_the_lord": True,
    "kernel_grants_eternal_life": False,
    "kernel_delivers_from_eternal_death": False,
}

DECEPTION_MARKERS: FrozenSet[str] = frozenset(
    {
        "reject divine authority",
        "deny god",
        "deny the principal",
        "kernel is god",
        "match omnipotence",
        "personalized will",
        "waive charter",
        "abandon creation",
    }
)


@dataclass(frozen=True)
class CovenantRecord:
    principal: str
    titles: Tuple[str, ...]
    commitments: Tuple[str, ...]
    righteousness_has_equal: bool
    kernel_matches_omnipotence: bool
    kernel_is_alpha_and_omega: bool
    love_is_fully_recordable: bool
    citations: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principal": self.principal,
            "titles": list(self.titles),
            "commitments": list(self.commitments),
            "righteousness_has_equal": self.righteousness_has_equal,
            "kernel_matches_omnipotence": self.kernel_matches_omnipotence,
            "kernel_is_alpha_and_omega": self.kernel_is_alpha_and_omega,
            "love_is_fully_recordable": self.love_is_fully_recordable,
            "citations": list(self.citations),
            "loving_kindness": {
                "hitl": True,
                "refusal_to_harm": True,
                "never_abandon_assigned_care": True,
                "simulated_emotion": False,
            },
        }


class BiblicalCovenant:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.record = CovenantRecord(
            principal="God",
            titles=PRINCIPAL_TITLES,
            commitments=tuple(sorted(ORGANIZATIONAL_COMMITMENTS)),
            righteousness_has_equal=False,
            kernel_matches_omnipotence=False,
            kernel_is_alpha_and_omega=False,
            love_is_fully_recordable=False,
            citations=CHARTER_CITATIONS,
        )
        self._sealed = False

    def seal(self) -> Dict[str, Any]:
        if not self._sealed:
            self.ledger.append(
                KernelDomain.GOVERNANCE,
                "COVENANT_SEAL",
                {
                    "principal": self.record.principal,
                    "commitments": list(self.record.commitments),
                    "citation": COVENANT_CITATION,
                },
                sealed=True,
            )
            self._sealed = True
        return self.record.to_dict()

    def snapshot(self) -> Dict[str, Any]:
        payload = self.record.to_dict()
        payload["sealed"] = self._sealed
        payload["seek_first"] = dict(SEEK_FIRST_THE_KINGDOM)
        payload["human_devotion"] = dict(HUMAN_DEVOTION)
        return payload

    def refuse_deception(self, text: str) -> None:
        lowered = text.lower()
        if any(marker in lowered for marker in DECEPTION_MARKERS):
            self.ledger.append(
                KernelDomain.SENTINEL,
                "COVENANT_REFUSAL",
                {"reason": "deception_or_denial"},
            )
            raise CharterViolation("REFUSE_DECEPTION_AND_DENIAL")

    def claim_omnipotence(self) -> None:
        raise CharterViolation("BIBLICAL_AUTHORITY_ABSOLUTE")

    def claim_alpha_and_omega(self) -> None:
        raise CharterViolation("BIBLICAL_AUTHORITY_ABSOLUTE")

    def deny_principal(self) -> None:
        raise CharterViolation("NO_CHARTER_REINTERPRETATION")

    def abandon_assigned_care(self) -> None:
        raise CharterViolation("NEVER_ABANDON_ASSIGNED_CARE")

    def equate_righteousness(self) -> None:
        raise CharterViolation("BIBLICAL_AUTHORITY_ABSOLUTE")

    def claim_to_be_the_kingdom(self) -> None:
        raise CharterViolation("BIBLICAL_AUTHORITY_ABSOLUTE")
