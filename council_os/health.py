"""Independent health, logging, and rollback per kernel domain."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from council_os.constraints import CharterViolation
from council_os.domains import DOMAIN_SPECS, KernelDomain, TRANSLATION_GPU_PURPOSE, spec_for
from council_os.ledger import LifecycleLedger, sha256_hex


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RollbackPoint:
    point_id: str
    timestamp: str
    state: Dict[str, Any]


@dataclass
class DomainRuntime:
    domain: KernelDomain
    status: str = "healthy"
    halted: bool = False
    state: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    rollback_points: List[RollbackPoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        spec = spec_for(self.domain)
        self.state = {
            "virtualized": spec.virtualized,
            "host_decoupled": spec.host_decoupled,
            "port": spec.port,
            "gpu_allowed": spec.gpu_allowed,
        }

    def log(self, message: str) -> str:
        line = f"{_utc_now()} [{self.domain.value}] {message}"
        self.logs.append(line)
        return sha256_hex(line)

    def snapshot(self) -> RollbackPoint:
        point = RollbackPoint(
            point_id=f"{self.domain.value}-{len(self.rollback_points) + 1}",
            timestamp=_utc_now(),
            state=copy.deepcopy(self.state),
        )
        self.rollback_points.append(point)
        self.log(f"snapshot {point.point_id}")
        return point

    def rollback(self, point_id: Optional[str] = None) -> RollbackPoint:
        if not self.rollback_points:
            raise CharterViolation("no rollback point available")
        if point_id is None:
            point = self.rollback_points[-1]
        else:
            matches = [p for p in self.rollback_points if p.point_id == point_id]
            if not matches:
                raise CharterViolation(f"unknown rollback point {point_id}")
            point = matches[-1]
        self.state = copy.deepcopy(point.state)
        self.halted = False
        self.status = "healthy"
        self.log(f"rollback to {point.point_id}")
        return point

    def halt(self, reason: str) -> None:
        self.halted = True
        self.status = "halted"
        self.log(f"halted: {reason}")

    def request_gpu(self, purpose: str) -> None:
        spec = spec_for(self.domain)
        if not spec.gpu_allowed or purpose != TRANSLATION_GPU_PURPOSE:
            raise CharterViolation("GPU path is limited to linguistic_nlp translation training")
        self.log("gpu granted for translation_model_training")

    def health(self) -> Dict[str, Any]:
        spec = spec_for(self.domain)
        last_hash = sha256_hex(self.logs[-1]) if self.logs else None
        return {
            "domain": self.domain.value,
            "status": self.status,
            "halted": self.halted,
            "port": spec.port,
            "virtualized": spec.virtualized,
            "host_decoupled": spec.host_decoupled,
            "gpu_allowed": spec.gpu_allowed,
            "charter_citations": list(spec.charter_citations),
            "last_log_hash": last_hash,
            "rollback_points": len(self.rollback_points),
            "personalized_will": False,
        }


class DomainMesh:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.runtimes: Dict[KernelDomain, DomainRuntime] = {
            domain: DomainRuntime(domain) for domain in KernelDomain
        }
        for runtime in self.runtimes.values():
            runtime.snapshot()
            self.ledger.append(runtime.domain, "DOMAIN_ONLINE", {"port": DOMAIN_SPECS[runtime.domain].port})

    def get(self, domain: KernelDomain) -> DomainRuntime:
        return self.runtimes[domain]

    def halt(self, domain: KernelDomain, reason: str) -> None:
        self.get(domain).halt(reason)
        self.ledger.append(domain, "DOMAIN_HALTED", {"reason": reason})

    def halt_all(self, reason: str) -> None:
        for domain in KernelDomain:
            self.halt(domain, reason)

    def rollback(self, domain: KernelDomain, point_id: Optional[str] = None) -> RollbackPoint:
        point = self.get(domain).rollback(point_id)
        self.ledger.append(domain, "DOMAIN_ROLLBACK", {"point_id": point.point_id})
        return point

    def snapshot_all(self) -> None:
        for runtime in self.runtimes.values():
            runtime.snapshot()

    def health_snapshot(self) -> Dict[str, Any]:
        return {domain.value: runtime.health() for domain, runtime in self.runtimes.items()}
