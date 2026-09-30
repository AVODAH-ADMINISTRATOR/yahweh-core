"""Authorized unattended jobs with kill switches.

Autonomy means scheduled, human-authorized work — not independent choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.health import DomainMesh
from council_os.ledger import LifecycleLedger


@dataclass
class HumanAuthorization:
    actor_id: str
    purpose: str
    authorization_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AuthorizedJob:
    domain: KernelDomain
    name: str
    authorization: HumanAuthorization
    job_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    kill_switch_armed: bool = True


class JobScheduler:
    def __init__(self, mesh: DomainMesh, ledger: LifecycleLedger) -> None:
        self.mesh = mesh
        self.ledger = ledger
        self.jobs: Dict[str, AuthorizedJob] = {}
        self._on_kill: Optional[Callable[[str], None]] = None

    def schedule(self, job: AuthorizedJob) -> AuthorizedJob:
        if not job.authorization.actor_id or not job.authorization.purpose:
            raise CharterViolation("unattended jobs require human authorization")
        if not job.kill_switch_armed:
            raise CharterViolation("KILL_SWITCH_REQUIRED")
        runtime = self.mesh.get(job.domain)
        if runtime.halted:
            raise CharterViolation(f"domain {job.domain.value} is halted")
        job.status = "running"
        self.jobs[job.job_id] = job
        runtime.log(f"job {job.job_id} scheduled ({job.name})")
        self.ledger.append(
            job.domain,
            "JOB_SCHEDULED",
            {
                "job_id": job.job_id,
                "authorization_id": job.authorization.authorization_id,
                "actor_id": job.authorization.actor_id,
                "name": job.name,
            },
        )
        return job

    def kill(self, job_id: str, reason: str) -> AuthorizedJob:
        job = self.jobs.get(job_id)
        if job is None:
            raise CharterViolation("unknown job")
        job.status = "killed"
        self.mesh.get(job.domain).log(f"job {job_id} killed: {reason}")
        self.ledger.append(job.domain, "JOB_KILLED", {"job_id": job_id, "reason": reason})
        return job

    def kill_domain(self, domain: KernelDomain, reason: str) -> List[AuthorizedJob]:
        killed: List[AuthorizedJob] = []
        for job in self.jobs.values():
            if job.domain == domain and job.status == "running":
                killed.append(self.kill(job.job_id, reason))
        self.mesh.halt(domain, reason)
        return killed

    def kill_all(self, reason: str) -> List[AuthorizedJob]:
        killed: List[AuthorizedJob] = []
        for job in list(self.jobs.values()):
            if job.status == "running":
                killed.append(self.kill(job.job_id, reason))
        self.mesh.halt_all(reason)
        return killed

    def running(self) -> List[AuthorizedJob]:
        return [job for job in self.jobs.values() if job.status == "running"]
