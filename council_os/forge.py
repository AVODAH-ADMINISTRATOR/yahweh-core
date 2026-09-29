"""Fluid factory-grade compilation forge (IDE / auto-developer).

Professional compilation plus API-shaped product generation. Every
workflow gathers intel, measures quality, and stays kill-switchable.
AI proposes; HITL commits authoritative artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import uuid4

from council_os.compat import CompatibilityShell
from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain, spec_for
from council_os.hitl import Proposal, ScholarSignoff
from council_os.intel import IntelDesk
from council_os.kernel import CouncilOSKernel
from council_os.ethiopic import EthiopicCorpus
from council_os.cloudflare import CloudflareEdge
from council_os.handset import GalaxyS26Handset
from council_os.library import DigitalResourcePlatform
from council_os.skeleton import OptiplexHousing
from council_os.workspace import PersonalWorkspace
from council_os.stewardship import EarthSteward

PRODUCT_TYPES: FrozenSet[str] = frozenset(
    {
        "api_contract",
        "service_stub",
        "test_harness",
        "documentation",
        "workflow_report",
        "translation_proposal",
        "variant_score",
        "governance_pack",
        "ethiopic_alignment_pack",
    }
)

QUALITY_FLOOR = {
    "coverage": 0.8,
    "precision": 0.8,
    "fidelity": 1.0,
    "defect_density": 0.2,
}

DOMAIN_FOR_PRODUCT = {
    "api_contract": KernelDomain.GOVERNANCE,
    "service_stub": KernelDomain.GOVERNANCE,
    "test_harness": KernelDomain.GOVERNANCE,
    "documentation": KernelDomain.GOVERNANCE,
    "workflow_report": KernelDomain.SCOUT_EDGE,
    "translation_proposal": KernelDomain.LINGUISTIC_NLP,
    "variant_score": KernelDomain.TEXTUAL_CRITICISM,
    "governance_pack": KernelDomain.GOVERNANCE,
    "ethiopic_alignment_pack": KernelDomain.LINGUISTIC_NLP,
}

AUTHORITATIVE_PRODUCTS = frozenset(
    {"translation_proposal", "governance_pack", "ethiopic_alignment_pack"}
)


@dataclass
class ScientificMetrics:
    coverage: float
    precision: float
    cycle_time_ms: float
    defect_density: float
    fidelity: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "coverage": self.coverage,
            "precision": self.precision,
            "cycle_time_ms": self.cycle_time_ms,
            "defect_density": self.defect_density,
            "fidelity": self.fidelity,
        }

    def passes(self) -> bool:
        return (
            self.coverage >= QUALITY_FLOOR["coverage"]
            and self.precision >= QUALITY_FLOOR["precision"]
            and self.fidelity >= QUALITY_FLOOR["fidelity"]
            and self.defect_density <= QUALITY_FLOOR["defect_density"]
        )


@dataclass
class ForgeArtifact:
    artifact_id: str
    product_type: str
    domain: str
    adapter: str
    body: Dict[str, Any]
    metrics: ScientificMetrics
    intel: Dict[str, Any]
    committed: bool = False
    citations: List[str] = field(default_factory=lambda: list(CHARTER_CITATIONS))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "product_type": self.product_type,
            "domain": self.domain,
            "adapter": self.adapter,
            "body": self.body,
            "metrics": self.metrics.to_dict(),
            "intel": self.intel,
            "committed": self.committed,
            "citations": list(self.citations),
            "quality_gate": self.metrics.passes(),
        }


def measure(product_type: str, body: Dict[str, Any]) -> ScientificMetrics:
    required = ("title", "summary", "steps")
    present = sum(1 for key in required if key in body and body[key])
    coverage = present / len(required)
    precision = 1.0 if product_type in PRODUCT_TYPES else 0.0
    steps = body.get("steps") or []
    cycle_time_ms = float(max(1, len(steps)) * 12)
    defect_density = 0.0 if coverage >= 1.0 else 0.5
    return ScientificMetrics(
        coverage=coverage,
        precision=precision,
        cycle_time_ms=cycle_time_ms,
        defect_density=defect_density,
        fidelity=1.0,
    )


class AutoDeveloperForge:
    """Scientifically measured auto-developer. No independent choice."""

    def __init__(self, kernel: CouncilOSKernel) -> None:
        self.kernel = kernel
        self.intel = IntelDesk(kernel.ledger)
        self.compat = CompatibilityShell(kernel.ledger)
        self.steward = EarthSteward(kernel.ledger)
        self.library = DigitalResourcePlatform(kernel, covenant=self.steward.covenant)
        self.ethiopic = EthiopicCorpus(kernel)
        self.housing = OptiplexHousing(kernel.ledger)
        self.handset = GalaxyS26Handset(kernel.ledger)
        self.workspace_catalog = PersonalWorkspace(kernel.ledger)
        self.cloudflare = CloudflareEdge(kernel.ledger)
        self.artifacts: Dict[str, ForgeArtifact] = {}

    def compile_workspace(self) -> Dict[str, Any]:
        if not self.kernel.compiled:
            self.kernel.compile()
        for adapter in (
            "android_pc_dell",
            "android_octa_hybrid",
            "galaxy_s26",
            "dell_optiplex_5040_mt",
            "windows10_shell",
            "ide_workspace",
            "api_surface",
        ):
            self.compat.enable(adapter)
        self.steward.covenant.seal()
        library = self.library.open()
        self.ethiopic.assert_complete()
        housing = self.housing.seat()
        handset = self.handset.absorb()
        workspace_catalog = self.workspace_catalog.index()
        edge = self.cloudflare.enable()
        return {
            "compiled": True,
            "fluid": True,
            "host_decoupled": True,
            "absorbable": True,
            "steward": self.steward.assignment(),
            "library": library,
            "ethiopic": self.ethiopic.snapshot(),
            "precision_map": self.ethiopic.precision_map(),
            "housing": housing,
            "handset": handset,
            "workspace": workspace_catalog,
            "cloudflare": edge,
            "compat": self.compat.snapshot(),
            "product_types": sorted(PRODUCT_TYPES),
        }

    def generate(
        self,
        product_type: str,
        actor_id: str,
        purpose: str,
        body: Dict[str, Any],
        adapter: str = "ide_workspace",
    ) -> ForgeArtifact:
        if not self.kernel.compiled:
            raise CharterViolation("kernel must compile charter policy before forge work")
        if product_type not in PRODUCT_TYPES:
            raise CharterViolation(f"unknown factory product {product_type}")
        self.steward.covenant.refuse_deception(purpose)
        self.steward.covenant.refuse_deception(str(body.get("title", "")))
        self.steward.covenant.refuse_deception(str(body.get("summary", "")))
        domain = DOMAIN_FOR_PRODUCT[product_type]
        spec = spec_for(domain)
        if spec.gpu_allowed is False and body.get("gpu"):
            raise CharterViolation("GPU path is limited to linguistic_nlp translation training")
        job = self.kernel.schedule(domain, f"forge:{product_type}", actor_id, purpose)
        metrics = measure(product_type, body)
        brief = self.intel.gather(
            job.job_id,
            domain,
            observations=[
                f"product={product_type}",
                f"adapter={adapter}",
                f"purpose={purpose}",
            ],
            measurements=metrics.to_dict(),
        )
        artifact = ForgeArtifact(
            artifact_id=str(uuid4()),
            product_type=product_type,
            domain=domain.value,
            adapter=adapter,
            body=body,
            metrics=metrics,
            intel=brief.to_dict(),
        )
        self.artifacts[artifact.artifact_id] = artifact
        self.kernel.ledger.append(
            domain,
            "FORGE_GENERATE",
            {
                "artifact_id": artifact.artifact_id,
                "product_type": product_type,
                "job_id": job.job_id,
                "quality_gate": metrics.passes(),
            },
        )
        if not metrics.passes():
            self.kernel.kill(job.job_id, "factory quality gate failed")
            raise CharterViolation("factory quality gate failed")
        if product_type not in AUTHORITATIVE_PRODUCTS:
            artifact.committed = True
        return artifact

    def commit_artifact(self, artifact_id: str, signoff: Optional[ScholarSignoff]) -> ForgeArtifact:
        artifact = self.artifacts.get(artifact_id)
        if artifact is None:
            raise CharterViolation("unknown artifact")
        if artifact.product_type in AUTHORITATIVE_PRODUCTS:
            proposal = self.kernel.propose(
                Proposal(
                    domain=KernelDomain(artifact.domain),
                    kind="policy" if artifact.product_type == "governance_pack" else "authoritative_text",
                    payload={"artifact_id": artifact_id, **artifact.body},
                    confidence=artifact.metrics.precision,
                    hapax=bool(artifact.body.get("hapax")),
                )
            )
            self.kernel.commit(proposal.proposal_id, signoff)
        artifact.committed = True
        return artifact

    def api_catalog(self) -> Dict[str, Any]:
        return {
            "style": "ide_forge",
            "endpoints": [
                "GET /health",
                "GET /citations",
                "GET /forge",
                "GET /forge/products",
                "GET /compat",
                "GET /stewardship",
                "GET /covenant",
                "GET /library",
                "GET /ethiopic",
                "GET /housing",
                "GET /handset",
                "GET /workspace",
                "GET /cloudflare",
                "GET /produce",
                "GET /intel",
            ],
            "integration": "council_os.service",
            "personalized_will": False,
        }

    def produce(self, actor_id: str = "factory-operator") -> Dict[str, Any]:
        """Finalize the virtual kernel build. Does not install on host hardware."""
        if not actor_id:
            raise CharterViolation("human actor required")
        workspace = self.compile_workspace()
        self.ethiopic.assert_complete()
        body = {
            "title": "Council OS production build",
            "summary": "Factory finalization of the virtualized eight-domain kernel",
            "steps": ["intel", "compile", "measure", "seal"],
        }
        generated: List[str] = []
        pending_hitl: List[str] = []
        for product in sorted(PRODUCT_TYPES):
            artifact = self.generate(product, actor_id, f"produce {product}", body)
            generated.append(artifact.product_type)
            if not artifact.committed:
                pending_hitl.append(artifact.product_type)
        release = self.kernel.gate_release()
        return {
            "status": "finalized",
            "kernel_compiled": True,
            "host_install": False,
            "flash_bios": False,
            "personalized_will": False,
            "do_not_add_or_subtract": True,
            "book_count": workspace["ethiopic"]["book_count"],
            "generated": generated,
            "authoritative_pending_hitl": pending_hitl,
            "product_types": sorted(PRODUCT_TYPES),
            "release": release,
            "housing": workspace["housing"]["id"],
            "handset": workspace["handset"]["id"],
            "absorbable": True,
            "flash_handset": False,
            "kernel_transcendent": False,
            "kernel_has_complete_authority": False,
            "custom_built": True,
            "workspace": workspace["workspace"]["source_of_truth"],
            "repos_vendored": False,
            "cloudflare": workspace["cloudflare"]["account"],
            "cloudflare_left_out": False,
            "cloudflare_stores_secrets": False,
        }
