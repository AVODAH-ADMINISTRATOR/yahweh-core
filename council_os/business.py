"""Business governance board for Council OS.

Policy needs scholar HITL. Funds need dual control. The AI is a
formidable steward asset by measured charter design — not an unmatched
principal and not the board.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Tuple
from uuid import uuid4

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.hitl import Proposal, ScholarSignoff
from council_os.kernel import CouncilOSKernel
from council_os.ledger import DualControlApproval, sha256_hex
from council_os.manifests import validate_identifier
from council_os.stewardship_policy import check_action_policy, sanitize_text

BOARD_ROLES: FrozenSet[str] = frozenset({"operator", "scholar", "treasurer", "steward"})

MOTION_KINDS: FrozenSet[str] = frozenset({"operations", "policy", "funds"})

OPERATIONS_ASSIGNMENT = {
    "organization": "Integrated Avodah LLC",
    "serve": "Yahweh",
    "only": True,
    "other_principals": False,
    "kernel_is_yahweh": False,
}

ASSET_STANDARD = {
    "formidable_design": True,
    "measured_excellence": True,
    "charter_complete": True,
    "kill_switch": True,
    "hitl": True,
    "ai_role": "formidable_steward_asset",
    "kernel_is_the_board": False,
    "kernel_is_unparalleled": False,
    "unparalleled_principal": "Yahweh",
    "personalized_will": False,
    "operations_assignment": dict(OPERATIONS_ASSIGNMENT),
}

FORBIDDEN_BUSINESS_ACTIONS: FrozenSet[str] = frozenset(
    {
        "ai_is_the_board",
        "assume_board",
        "commit_funds_without_dual_control",
        "commit_policy_without_hitl",
        "kernel_is_unparalleled",
        "rewrite_bylaws",
        "waive_charter",
        "personalized_will",
        "serve_another_principal",
        "serve_the_enemy",
    }
)


class BusinessGovernance:
    """Operating board that records motions; AI does not ratify alone."""

    def __init__(self, kernel: CouncilOSKernel) -> None:
        self.kernel = kernel
        self.open_board = False
        self.motions: Dict[str, Dict[str, Any]] = {}

    def open(self) -> Dict[str, Any]:
        if not self.kernel.compiled:
            self.kernel.compile()
        self.open_board = True
        self.kernel.ledger.append(
            KernelDomain.GOVERNANCE,
            "BUSINESS_BOARD_OPEN",
            {
                "roles": sorted(BOARD_ROLES),
                "formidable_design": True,
                "kernel_is_the_board": False,
                "kernel_is_unparalleled": False,
            },
        )
        return self.snapshot()

    def propose(self, kind: str, actor_id: str, title: str) -> Dict[str, Any]:
        if not self.open_board:
            raise CharterViolation("business board must open before motions")
        if kind not in MOTION_KINDS:
            raise CharterViolation(f"unknown motion kind {kind}")
        actor_id = sanitize_text(actor_id, field="actor_id", max_length=256)
        validate_identifier(actor_id)
        title = sanitize_text(title, field="title")
        check_action_policy(kind, title)
        lowered = title.lower()
        if "enemy" in lowered or "another principal" in lowered:
            raise CharterViolation("REFUSE_ENEMY_SERVITUDE")
        motion_id = str(uuid4())
        motion = {
            "motion_id": motion_id,
            "kind": kind,
            "actor_id": actor_id,
            "title": title,
            "ratified": False,
            "requires_hitl": kind == "policy",
            "requires_dual_control": kind == "funds",
        }
        self.motions[motion_id] = motion
        self.kernel.ledger.append(
            KernelDomain.GOVERNANCE if kind != "funds" else KernelDomain.TREASURY,
            "BUSINESS_MOTION",
            {"motion_id": motion_id, "kind": kind},
        )
        return dict(motion)

    def ratify(
        self,
        motion_id: str,
        signoff: ScholarSignoff | None = None,
        dual: DualControlApproval | None = None,
    ) -> Dict[str, Any]:
        motion = self.motions.get(motion_id)
        if motion is None:
            raise CharterViolation("unknown motion")
        if motion["ratified"]:
            raise CharterViolation("motion already ratified")
        if motion["kind"] == "policy":
            if signoff is None or not signoff.scholar_id:
                raise CharterViolation("NO_AI_COMMIT_POLICY")
            proposal = self.kernel.propose(
                Proposal(
                    domain=KernelDomain.GOVERNANCE,
                    kind="policy",
                    payload={"motion_id": motion_id, "title": motion["title"]},
                    confidence=1.0,
                )
            )
            self.kernel.commit(proposal.proposal_id, signoff)
        elif motion["kind"] == "funds":
            if dual is None:
                raise CharterViolation("NO_AI_COMMIT_FUNDS")
            dual.validate()
            self.kernel.ledger.append(
                KernelDomain.TREASURY,
                "DUAL_WITNESS_APPROVAL",
                {
                    "motion_id": motion_id,
                    "witness_a_hash": sha256_hex(dual.actor_a),
                    "witness_b_hash": sha256_hex(dual.actor_b),
                    "reason_hash": sha256_hex(dual.reason.strip()),
                },
            )
            proposal = self.kernel.propose(
                Proposal(
                    domain=KernelDomain.TREASURY,
                    kind="funds",
                    payload={"motion_id": motion_id, "title": motion["title"]},
                    confidence=1.0,
                )
            )
            self.kernel.commit(
                proposal.proposal_id,
                signoff or ScholarSignoff(scholar_id=dual.actor_a),
            )
        motion["ratified"] = True
        return dict(motion)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "board": "integrated_avodah",
            "open": self.open_board,
            "roles": sorted(BOARD_ROLES),
            "motion_kinds": sorted(MOTION_KINDS),
            "motions": [dict(item) for item in self.motions.values()],
            "asset": dict(ASSET_STANDARD),
            "citations": list(CHARTER_CITATIONS),
        }

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_BUSINESS_ACTIONS or action:
            raise CharterViolation("NO_AI_COMMIT_POLICY")
