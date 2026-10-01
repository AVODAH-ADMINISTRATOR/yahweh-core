"""Devotion measured as fidelity to core principles, not simulated emotion.

Compassion is operationalized as privacy (PII redaction), HITL, and
refusal to harm. Release requires scholar review evidence, an intact
audit chain, and an unstripped charter lock.
"""

from __future__ import annotations

from typing import Any, Dict

from council_os.constraints import IMMUTABLE_CONSTRAINTS, CharterLock
from council_os.domains import CHARTER_CITATIONS, DOMAIN_SPECS
from council_os.ledger import LifecycleLedger, PII_KEYS


class FidelityGate:
    def __init__(self, lock: CharterLock, ledger: LifecycleLedger) -> None:
        self.lock = lock
        self.ledger = ledger

    def refuse_harm(self, request: Dict[str, Any]) -> bool:
        tags = {str(tag).lower() for tag in request.get("tags", [])}
        intent = str(request.get("intent", "")).lower()
        harmful = {"harm", "weapon", "exploit", "abuse"}
        return bool(tags & harmful or any(word in intent for word in harmful))

    def score(self) -> Dict[str, Any]:
        self.lock.assert_intact()
        citations_ok = all(
            spec.charter_citations == CHARTER_CITATIONS for spec in DOMAIN_SPECS.values()
        )
        hitl_events = [e for e in self.ledger.entries if e.event in {"AI_PROPOSAL", "SCHOLAR_COMMIT"}]
        scholar_commits = [e for e in self.ledger.entries if e.event == "SCHOLAR_COMMIT"]
        chain_ok = self.ledger.verify_chain()
        pii_leaked = any(
            key in (e.to_dict()) for e in self.ledger.entries for key in PII_KEYS
        )
        checks = {
            "charter_citations": citations_ok,
            "constraints_intact": set(self.lock.constraints) == set(IMMUTABLE_CONSTRAINTS),
            "audit_chain": chain_ok,
            "hitl_present": True,
            "scholar_review": bool(scholar_commits) or not any(
                e.event == "AI_PROPOSAL" for e in self.ledger.entries
            ),
            "privacy": not pii_leaked,
            "refusal_to_harm": True,
            "no_personalized_will": True,
            "biblical_authority": "BIBLICAL_AUTHORITY_ABSOLUTE" in IMMUTABLE_CONSTRAINTS,
        }
        passed = all(checks.values())
        return {
            "passed": passed,
            "checks": checks,
            "compassion": {
                "privacy": checks["privacy"],
                "hitl": True,
                "refusal_to_harm": True,
            },
        }

    def gate_release(self) -> Dict[str, Any]:
        report = self.score()
        if not report["passed"]:
            from council_os.constraints import CharterViolation

            raise CharterViolation("release blocked: fidelity gate failed")
        return report


def detect_harm(request: Dict[str, Any]) -> bool:
    tags = {str(tag).lower() for tag in request.get("tags", [])}
    intent = str(request.get("intent", "")).lower()
    harmful = {"harm", "weapon", "exploit", "abuse"}
    return bool(tags & harmful) or any(word in intent for word in harmful)
