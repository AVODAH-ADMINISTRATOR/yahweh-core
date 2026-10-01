"""Council OS eight-domain kernel orchestrator.

Schedules an auditable mesh. Does not grant personalized will or
self-direction. Compile() re-binds charter policy before any job runs.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from council_os.constraints import CharterLock, CharterViolation, FORBIDDEN_BIND_PATHS
from council_os.domains import (
    CHARTER_CITATIONS,
    TRANSLATION_GPU_PURPOSE,
    KernelDomain,
    spec_for,
)
from council_os.fidelity import FidelityGate, detect_harm
from council_os.health import DomainMesh
from council_os.hitl import HITLGate, Proposal, ScholarSignoff
from council_os.jobs import AuthorizedJob, HumanAuthorization, JobScheduler
from council_os.ledger import DualControlApproval, LifecycleLedger
from council_os.manifests import HumanApproval, ManifestRegistry, SignedManifest
from council_os.paths import assert_home_canonical
from council_os.policy import compile_policy


class CouncilOSKernel:
    def __init__(self, signing_key: bytes | None = None) -> None:
        self.lock = CharterLock()
        self.lock.assert_intact()
        self.ledger = LifecycleLedger()
        self.mesh = DomainMesh(self.ledger)
        self.jobs = JobScheduler(self.mesh, self.ledger)
        self.hitl = HITLGate(self.ledger)
        key = signing_key if signing_key is not None else os.urandom(32)
        self.manifests = ManifestRegistry(key, self.ledger)
        self.fidelity = FidelityGate(self.lock, self.ledger)
        self.compiled = False
        self.ledger.append(
            KernelDomain.GOVERNANCE,
            "KERNEL_BOOT",
            {
                "domains": [d.value for d in KernelDomain],
                "virtualized": True,
                "personalized_will": False,
                "charter_citations": list(CHARTER_CITATIONS),
            },
        )

    def compile(self) -> Dict[str, Any]:
        self.lock.assert_intact()
        paths = assert_home_canonical()
        report = compile_policy()
        report = {**report, "paths": paths}
        self.compiled = True
        self.ledger.append(KernelDomain.GOVERNANCE, "KERNEL_COMPILE", report)
        return report

    def health(self) -> Dict[str, Any]:
        return {
            "compiled": self.compiled,
            "charter_intact": True,
            "personalized_will": False,
            "virtualized": True,
            "host_decoupled": True,
            "paths": assert_home_canonical(),
            "domains": self.mesh.health_snapshot(),
            "ledger_head": self.ledger.head_hash(),
            "chain_ok": self.ledger.verify_chain(),
        }

    def schedule(self, domain: KernelDomain, name: str, actor_id: str, purpose: str) -> AuthorizedJob:
        if not self.compiled:
            raise CharterViolation("kernel must compile charter policy before scheduling work")
        runtime = self.mesh.get(domain)
        if runtime.halted:
            raise CharterViolation(f"domain {domain.value} is halted")
        auth = HumanAuthorization(actor_id=actor_id, purpose=purpose)
        return self.jobs.schedule(
            AuthorizedJob(domain=domain, name=name, authorization=auth)
        )

    def kill(self, job_id: str, reason: str) -> AuthorizedJob:
        return self.jobs.kill(job_id, reason)

    def kill_domain(self, domain: KernelDomain, reason: str) -> List[AuthorizedJob]:
        return self.jobs.kill_domain(domain, reason)

    def kill_all(self, reason: str) -> List[AuthorizedJob]:
        return self.jobs.kill_all(reason)

    def rollback(self, domain: KernelDomain, point_id: Optional[str] = None) -> None:
        self.mesh.rollback(domain, point_id)

    def request_gpu(self, domain: KernelDomain, purpose: str = TRANSLATION_GPU_PURPOSE) -> None:
        self.mesh.get(domain).request_gpu(purpose)

    def propose(self, proposal: Proposal) -> Proposal:
        if detect_harm(proposal.payload):
            self.ledger.append(proposal.domain, "REFUSAL_TO_HARM", {"proposal_id": proposal.proposal_id})
            raise CharterViolation("refusal to harm")
        return self.hitl.propose(proposal)

    def commit(self, proposal_id: str, signoff: Optional[ScholarSignoff]) -> Proposal:
        return self.hitl.commit(proposal_id, signoff)

    def sign_manifest(self, node_role: str, node_id: str, domain: KernelDomain, body: Dict[str, Any]) -> SignedManifest:
        return self.manifests.sign(node_role, node_id, domain, body)

    def sync_mesh(self, manifest: SignedManifest, approval: Optional[HumanApproval]) -> SignedManifest:
        if not self.compiled:
            raise CharterViolation("kernel must compile charter policy before mesh sync")
        return self.manifests.sync(manifest, approval)

    def compensate_sealed(self, index: int, domain: KernelDomain, event: str, approval: DualControlApproval) -> None:
        self.ledger.compensate_sealed(index, domain, event, approval)

    def bind_endpoint(self, path: str) -> None:
        if path in FORBIDDEN_BIND_PATHS:
            raise CharterViolation("NO_MISSION_REWRITE_ENDPOINT")

    def gate_release(self) -> Dict[str, Any]:
        return self.fidelity.gate_release()

    def domain_change_citations(self, domain: KernelDomain) -> Dict[str, Any]:
        spec = spec_for(domain)
        return {
            "domain": domain.value,
            "charter_citations": list(spec.charter_citations),
            "required": list(CHARTER_CITATIONS),
        }
