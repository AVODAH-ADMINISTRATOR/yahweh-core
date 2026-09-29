"""Eight governed Council OS kernel domains.

Doubles the four Council OS quadrants (identity/ledger, communal integrity,
alliance bridge, operations/runtime) into eight explicit service boundaries.
Council OS remains virtualized and decoupled from host hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Tuple

CHARTER_CITATIONS: Tuple[str, str] = (
    "docs/linguistic_theological_charter.md",
    "docs/ethical_ai_governance.md",
)

TRANSLATION_GPU_PURPOSE = "translation_model_training"


class KernelDomain(str, Enum):
    IDENTITY = "identity"
    LEDGER = "ledger"
    LINGUISTIC_NLP = "linguistic_nlp"
    TEXTUAL_CRITICISM = "textual_criticism"
    SCOUT_EDGE = "scout_edge"
    GOVERNANCE = "governance"
    TREASURY = "treasury"
    SENTINEL = "sentinel"


DOMAIN_PORTS: dict[KernelDomain, int] = {
    KernelDomain.IDENTITY: 8101,
    KernelDomain.LEDGER: 8102,
    KernelDomain.LINGUISTIC_NLP: 8103,
    KernelDomain.TEXTUAL_CRITICISM: 8104,
    KernelDomain.SCOUT_EDGE: 8105,
    KernelDomain.GOVERNANCE: 8106,
    KernelDomain.TREASURY: 8107,
    KernelDomain.SENTINEL: 8108,
}


@dataclass(frozen=True)
class DomainSpec:
    domain: KernelDomain
    quadrant_origin: str
    description: str
    port: int
    gpu_allowed: bool
    charter_citations: Tuple[str, ...] = CHARTER_CITATIONS
    virtualized: bool = True
    host_decoupled: bool = True
    ai_may_propose: bool = True
    ai_may_commit_authoritative_text: bool = False
    ai_may_commit_funds: bool = False
    ai_may_commit_policy: bool = False


DOMAIN_SPECS: dict[KernelDomain, DomainSpec] = {
    KernelDomain.IDENTITY: DomainSpec(
        domain=KernelDomain.IDENTITY,
        quadrant_origin="identity/ledger",
        description="Zero-trust identity provider; hashed subject IDs only.",
        port=DOMAIN_PORTS[KernelDomain.IDENTITY],
        gpu_allowed=False,
    ),
    KernelDomain.LEDGER: DomainSpec(
        domain=KernelDomain.LEDGER,
        quadrant_origin="identity/ledger",
        description="Immutable SHA-256 lifecycle ledger with dual-control seals.",
        port=DOMAIN_PORTS[KernelDomain.LEDGER],
        gpu_allowed=False,
    ),
    KernelDomain.LINGUISTIC_NLP: DomainSpec(
        domain=KernelDomain.LINGUISTIC_NLP,
        quadrant_origin="communal integrity / scholarly work",
        description="Morphology, parse, and translation proposals; 8-GPU training path only.",
        port=DOMAIN_PORTS[KernelDomain.LINGUISTIC_NLP],
        gpu_allowed=True,
    ),
    KernelDomain.TEXTUAL_CRITICISM: DomainSpec(
        domain=KernelDomain.TEXTUAL_CRITICISM,
        quadrant_origin="communal integrity / scholarly work",
        description="Variant scoring with confidence tags; never silent authoritative commits.",
        port=DOMAIN_PORTS[KernelDomain.TEXTUAL_CRITICISM],
        gpu_allowed=False,
    ),
    KernelDomain.SCOUT_EDGE: DomainSpec(
        domain=KernelDomain.SCOUT_EDGE,
        quadrant_origin="alliance bridge",
        description="Scout/gateway/core mesh unified by signed manifests.",
        port=DOMAIN_PORTS[KernelDomain.SCOUT_EDGE],
        gpu_allowed=False,
    ),
    KernelDomain.GOVERNANCE: DomainSpec(
        domain=KernelDomain.GOVERNANCE,
        quadrant_origin="operations/runtime",
        description="Compliance, scholar review gates, and charter fidelity scoring.",
        port=DOMAIN_PORTS[KernelDomain.GOVERNANCE],
        gpu_allowed=False,
    ),
    KernelDomain.TREASURY: DomainSpec(
        domain=KernelDomain.TREASURY,
        quadrant_origin="operations/runtime",
        description="Stewardship accounting with zero-state value memory.",
        port=DOMAIN_PORTS[KernelDomain.TREASURY],
        gpu_allowed=False,
    ),
    KernelDomain.SENTINEL: DomainSpec(
        domain=KernelDomain.SENTINEL,
        quadrant_origin="operations/runtime",
        description="Isolation perimeter, kill switches, and refusal-to-harm.",
        port=DOMAIN_PORTS[KernelDomain.SENTINEL],
        gpu_allowed=False,
    ),
}


def all_domains() -> FrozenSet[KernelDomain]:
    return frozenset(KernelDomain)


def spec_for(domain: KernelDomain) -> DomainSpec:
    return DOMAIN_SPECS[domain]


def parse_domain(value: str) -> KernelDomain:
    try:
        return KernelDomain(value)
    except ValueError as exc:
        raise ValueError(f"unknown kernel domain: {value}") from exc
