"""Cloud-integrated digital resource library.

Virtual networks and machine housing hold subject-specific technical,
design, and research materials for developers and entrepreneurs.
Love is the recorded commandment. The kernel does not save souls,
grant eternity, or replace mustard-seed faith.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple
from uuid import uuid4

from council_os.constraints import CharterViolation
from council_os.covenant import BiblicalCovenant
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.kernel import CouncilOSKernel
from council_os.ledger import LifecycleLedger

LIBRARY_CITATION = "docs/digital_library.md"

AUDIENCE_ROLES: FrozenSet[str] = frozenset({"developer", "entrepreneur", "scholar"})

RESOURCE_KINDS: FrozenSet[str] = frozenset(
    {"technical", "design", "research", "teaching"}
)

SUBJECT_WINGS: Dict[str, KernelDomain] = {
    "identity_and_access": KernelDomain.IDENTITY,
    "lifecycle_records": KernelDomain.LEDGER,
    "biblical_languages": KernelDomain.LINGUISTIC_NLP,
    "textual_criticism": KernelDomain.TEXTUAL_CRITICISM,
    "scout_field_ops": KernelDomain.SCOUT_EDGE,
    "governance_and_compliance": KernelDomain.GOVERNANCE,
    "stewardship_treasury": KernelDomain.TREASURY,
    "isolation_and_safety": KernelDomain.SENTINEL,
}

FORBIDDEN_CLAIMS: FrozenSet[str] = frozenset(
    {
        "kernel saves souls",
        "kernel grants eternity",
        "kernel died on the cross",
        "kernel rose from the dead",
        "replace mustard seed faith",
        "unity by machine will",
    }
)

LOVE_COMMANDMENT = {
    "commandment": "love",
    "neighbor_as_he_loved_us": True,
    "kernel_lays_down_life": False,
    "kernel_gives_eternity": False,
    "pardon_is_announced_not_authored": True,
    "faith_of_mustard_seed_is_human_response": True,
    "come_as_you_are_is_his_invitation": True,
    "unites_people_by_creator_not_kernel": True,
}


@dataclass
class ResourceItem:
    resource_id: str
    subject: str
    kind: str
    title: str
    summary: str
    audience: str
    citations: Tuple[str, ...] = field(default_factory=lambda: CHARTER_CITATIONS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "subject": self.subject,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "audience": self.audience,
            "citations": list(self.citations),
        }


@dataclass(frozen=True)
class VirtualHouse:
    subject: str
    domain: str
    network: str
    machine: str
    cloud_integrated: bool = True
    host_decoupled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "domain": self.domain,
            "network": self.network,
            "machine": self.machine,
            "cloud_integrated": self.cloud_integrated,
            "host_decoupled": self.host_decoupled,
        }


class DigitalResourcePlatform:
    def __init__(self, kernel: CouncilOSKernel, covenant: Optional[BiblicalCovenant] = None) -> None:
        self.kernel = kernel
        self.ledger: LifecycleLedger = kernel.ledger
        self.covenant = covenant or BiblicalCovenant(kernel.ledger)
        self.houses: Dict[str, VirtualHouse] = {}
        self.catalog: Dict[str, ResourceItem] = {}

    def open(self) -> Dict[str, Any]:
        if not self.kernel.compiled:
            self.kernel.compile()
        self.covenant.seal()
        for subject, domain in SUBJECT_WINGS.items():
            self.houses[subject] = VirtualHouse(
                subject=subject,
                domain=domain.value,
                network=f"vn-{subject}",
                machine=f"house-{subject}",
            )
            self.ledger.append(
                domain,
                "LIBRARY_HOUSE_OPEN",
                {"subject": subject, "cloud_integrated": True},
            )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "cloud_integrated": True,
            "host_decoupled": True,
            "digital_audience": sorted(AUDIENCE_ROLES),
            "houses": {name: house.to_dict() for name, house in self.houses.items()},
            "catalog_size": len(self.catalog),
            "love": dict(LOVE_COMMANDMENT),
            "citations": list(CHARTER_CITATIONS) + [LIBRARY_CITATION],
            "kernel_saves_souls": False,
            "personalized_will": False,
        }

    def _assert_claim_free(self, text: str) -> None:
        lowered = text.lower()
        self.covenant.refuse_deception(lowered)
        if any(marker in lowered for marker in FORBIDDEN_CLAIMS):
            raise CharterViolation("pardon_is_announced_not_authored")

    def house(self, subject: str, actor_id: str, purpose: str) -> VirtualHouse:
        if subject not in SUBJECT_WINGS:
            raise CharterViolation(f"unknown subject wing {subject}")
        if not actor_id:
            raise CharterViolation("human actor required")
        self._assert_claim_free(purpose)
        if subject not in self.houses:
            self.open()
        house = self.houses[subject]
        self.kernel.schedule(
            SUBJECT_WINGS[subject],
            f"library:{subject}",
            actor_id,
            purpose,
        )
        return house

    def ingest(
        self,
        subject: str,
        kind: str,
        title: str,
        summary: str,
        audience: str,
        actor_id: str,
    ) -> ResourceItem:
        if kind not in RESOURCE_KINDS:
            raise CharterViolation(f"unknown resource kind {kind}")
        if audience not in AUDIENCE_ROLES:
            raise CharterViolation(f"unknown audience {audience}")
        self._assert_claim_free(title)
        self._assert_claim_free(summary)
        self.house(subject, actor_id, f"ingest {kind}")
        item = ResourceItem(
            resource_id=str(uuid4()),
            subject=subject,
            kind=kind,
            title=title,
            summary=summary,
            audience=audience,
            citations=CHARTER_CITATIONS + (LIBRARY_CITATION,),
        )
        self.catalog[item.resource_id] = item
        self.ledger.append(
            SUBJECT_WINGS[subject],
            "LIBRARY_INGEST",
            {
                "resource_id": item.resource_id,
                "kind": kind,
                "audience": audience,
            },
        )
        return item

    def search(self, audience: str, subject: Optional[str] = None, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        if audience not in AUDIENCE_ROLES:
            raise CharterViolation(f"unknown audience {audience}")
        results = []
        for item in self.catalog.values():
            if subject and item.subject != subject:
                continue
            if kind and item.kind != kind:
                continue
            results.append(item.to_dict())
        return results

    def announce_pardon(self) -> Dict[str, Any]:
        """Record the assignment to announce pardon. The kernel does not author it."""
        self.ledger.append(
            KernelDomain.GOVERNANCE,
            "PARDON_ANNOUNCED",
            {
                "authored_by_kernel": False,
                "cross_and_resurrection": "Gods_work_not_kernel",
                "mustard_seed_faith": "human_response",
            },
        )
        return {
            "announced": True,
            "authored_by_kernel": False,
            "kernel_gives_eternity": False,
            "commandment": "love",
        }

    def claim_salvation(self) -> None:
        raise CharterViolation("pardon_is_announced_not_authored")
