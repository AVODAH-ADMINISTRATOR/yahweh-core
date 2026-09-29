"""Human-in-the-loop gates for authoritative commits.

AI may propose parses, variants, and alignments. It must not commit
authoritative text, funds, or policy. Hapax forms require raw morphology
review rather than a hallucinated definitive answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.ledger import LifecycleLedger

AUTHORITATIVE_KINDS = frozenset({"authoritative_text", "funds", "policy"})
PROPOSAL_KINDS = frozenset({"parse", "variant", "alignment", "translation", "authoritative_text", "funds", "policy"})


@dataclass
class ScholarSignoff:
    scholar_id: str
    reviewed_raw_morphology: bool = False
    notes: str = ""


@dataclass
class Proposal:
    domain: KernelDomain
    kind: str
    payload: Dict[str, Any]
    confidence: float
    hapax: bool = False
    source: str = "ai"
    proposal_id: str = field(default_factory=lambda: str(uuid4()))
    committed: bool = False


class HITLGate:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.proposals: Dict[str, Proposal] = {}

    def propose(self, proposal: Proposal) -> Proposal:
        if proposal.kind not in PROPOSAL_KINDS:
            raise CharterViolation(f"unknown proposal kind {proposal.kind}")
        if not 0.0 <= proposal.confidence <= 1.0:
            raise CharterViolation("confidence must be tagged in [0, 1]")
        if proposal.source == "ai" and proposal.kind in AUTHORITATIVE_KINDS:
            # AI may file a proposal, never a commit.
            pass
        if proposal.hapax:
            proposal.payload.setdefault("display", "raw_morphology")
            proposal.payload["definitive_answer_suppressed"] = True
        self.proposals[proposal.proposal_id] = proposal
        self.ledger.append(
            proposal.domain,
            "AI_PROPOSAL",
            {
                "proposal_id": proposal.proposal_id,
                "kind": proposal.kind,
                "confidence": proposal.confidence,
                "hapax": proposal.hapax,
            },
        )
        return proposal

    def commit(self, proposal_id: str, signoff: Optional[ScholarSignoff]) -> Proposal:
        proposal = self.proposals.get(proposal_id)
        if proposal is None:
            raise CharterViolation("unknown proposal")
        if proposal.committed:
            raise CharterViolation("proposal already committed")
        missing_signoff = signoff is None or not signoff.scholar_id
        if missing_signoff and proposal.source == "ai" and proposal.kind in AUTHORITATIVE_KINDS:
            constraint = {
                "funds": "NO_AI_COMMIT_FUNDS",
                "policy": "NO_AI_COMMIT_POLICY",
                "authoritative_text": "NO_AI_COMMIT_AUTHORITATIVE_TEXT",
            }[proposal.kind]
            raise CharterViolation(constraint)
        if missing_signoff and (proposal.kind in AUTHORITATIVE_KINDS or proposal.source == "ai"):
            raise CharterViolation("HITL_REQUIRED_FOR_AUTHORITATIVE_COMMIT")
        if proposal.hapax and (signoff is None or not signoff.reviewed_raw_morphology):
            raise CharterViolation("HITL_REQUIRED_FOR_AUTHORITATIVE_COMMIT")
        proposal.committed = True
        self.ledger.append(
            proposal.domain,
            "SCHOLAR_COMMIT",
            {
                "proposal_id": proposal.proposal_id,
                "scholar_id": signoff.scholar_id if signoff else None,
                "kind": proposal.kind,
            },
            sealed=proposal.kind in AUTHORITATIVE_KINDS,
        )
        return proposal
