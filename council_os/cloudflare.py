"""Cloudflare edge catalog for Council OS.

Enabled Cloudflare products already cited in the charter (edge TLS,
routing, R2 archival) are recorded as a virtual account surface. API
tokens and origin credentials stay out of the kernel.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

EDGE_ACCOUNT = "cloudflare_enabled"

ENABLED_PRODUCTS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "edge_cdn",
        "role": "tls_perimeter",
        "citation": "docs/integrated_avodah_charter.md",
        "stores_secrets": False,
    },
    {
        "id": "dns",
        "role": "name_service",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
    {
        "id": "waf_routing",
        "role": "endpoint_obfuscation",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
    {
        "id": "workers",
        "role": "edge_compute",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
    {
        "id": "r2",
        "role": "zero_egress_archive",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
    {
        "id": "kv",
        "role": "edge_metadata",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
    {
        "id": "pages",
        "role": "static_workspace",
        "citation": "docs/digital_library.md",
        "stores_secrets": False,
    },
    {
        "id": "zero_trust",
        "role": "access_isolation",
        "citation": "docs/ethical_ai_governance.md",
        "stores_secrets": False,
    },
)

FORBIDDEN_EDGE_ACTIONS: FrozenSet[str] = frozenset(
    {
        "store_api_token",
        "absorb_credentials",
        "expose_origin_ip",
        "bypass_waf",
        "live_account_login",
        "wipe_host",
        "flash_handset",
    }
)


class CloudflareEdge:
    """Host-decoupled catalog of enabled Cloudflare products."""

    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.enabled = False

    def enable(self) -> Dict[str, Any]:
        self.enabled = True
        self.ledger.append(
            KernelDomain.SCOUT_EDGE,
            "CLOUDFLARE_ENABLE",
            {
                "account": EDGE_ACCOUNT,
                "products": [item["id"] for item in ENABLED_PRODUCTS],
                "stores_secrets": False,
                "live_login": False,
            },
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "account": EDGE_ACCOUNT,
            "enabled": self.enabled,
            "left_out": False,
            "virtualized": True,
            "host_decoupled": True,
            "stores_secrets": False,
            "live_login": False,
            "tls": "1.3",
            "products": [dict(item) for item in ENABLED_PRODUCTS],
            "payload_hashing": "sha256",
            "citations": list(CHARTER_CITATIONS),
            "kernel_has_complete_authority": False,
        }

    def refuse(self, action: str) -> None:
        normalized = str(action).strip()
        if normalized in FORBIDDEN_EDGE_ACTIONS or not normalized:
            raise CharterViolation("ZERO_TRUST_ISOLATION")
