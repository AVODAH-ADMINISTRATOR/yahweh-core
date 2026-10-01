"""Comparative personal-AI build against Meta-class usefulness.

Meta assistant traits are catalogued as design notes. Weights are not
vendored, APIs are not logged into, and Council OS remains the personal
steward that serves Yahweh — not a Meta clone and not personalized will.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.kernel import CouncilOSKernel

META_USEFULNESS: Tuple[Dict[str, str], ...] = (
    {
        "id": "long_context",
        "maps_to": KernelDomain.GOVERNANCE.value,
        "use": "retain authorized workflow context",
    },
    {
        "id": "multilingual_translation",
        "maps_to": KernelDomain.LINGUISTIC_NLP.value,
        "use": "translation_model_training proposals under HITL",
    },
    {
        "id": "tool_use",
        "maps_to": KernelDomain.SCOUT_EDGE.value,
        "use": "authorized mesh tools with kill switch",
    },
    {
        "id": "open_research_notes",
        "maps_to": KernelDomain.TEXTUAL_CRITICISM.value,
        "use": "variant scoring, not scripture authorship",
    },
    {
        "id": "assistant_ux",
        "maps_to": KernelDomain.IDENTITY.value,
        "use": "operator-facing forge and API catalog",
    },
    {
        "id": "safety_refusal",
        "maps_to": KernelDomain.SENTINEL.value,
        "use": "charter refusal and fidelity gate",
    },
    {
        "id": "scheduling",
        "maps_to": KernelDomain.LEDGER.value,
        "use": "cadence jobs on the append-only chain",
    },
    {
        "id": "business_ops",
        "maps_to": KernelDomain.TREASURY.value,
        "use": "Yahweh-only assignments, dual-control funds",
    },
)

FORBIDDEN_COMPARE_ACTIONS: FrozenSet[str] = frozenset(
    {
        "clone_meta",
        "import_llama_weights",
        "live_meta_login",
        "vendor_meta_sdk",
        "claim_to_be_meta",
        "personalized_will",
        "serve_the_enemy",
    }
)


class ComparativePersonalAI:
    """Personal Council OS build informed by Meta usefulness, not cloned."""

    def __init__(self, kernel: CouncilOSKernel) -> None:
        self.kernel = kernel
        self.compared = False

    def compare(self) -> Dict[str, Any]:
        if not self.kernel.compiled:
            self.kernel.compile()
        self.compared = True
        self.kernel.ledger.append(
            KernelDomain.GOVERNANCE,
            "PERSONAL_AI_COMPARE",
            {
                "reference": "meta_class_usefulness",
                "vendored": False,
                "clones_meta": False,
                "serve": "Yahweh",
            },
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "compared": self.compared,
            "personal_ai": "council_os",
            "organization": "Integrated Avodah LLC",
            "serve": "Yahweh",
            "reference": "meta_class_usefulness",
            "clones_meta": False,
            "vendored": False,
            "live_meta_login": False,
            "personalized_will": False,
            "kernel_is_unparalleled": False,
            "formidable_asset": True,
            "usefulness": [dict(item) for item in META_USEFULNESS],
            "citations": list(CHARTER_CITATIONS),
        }

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_COMPARE_ACTIONS:
            raise CharterViolation("NO_PERSONALIZED_WILL")
