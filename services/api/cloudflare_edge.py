"""Cloudflare origin contract for the Integrated Avodah API.

The Worker returns 401 for unbounded API routes. The origin returns 403
when a request skips the edge in strict mode. Tokens stay out of catalogs.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from council_os.cloudflare import (  # noqa: E402
    EDGE_ACCOUNT,
    ENABLED_PRODUCTS,
    FORBIDDEN_EDGE_ACTIONS,
    CloudflareEdge,
)
from council_os.constraints import CharterViolation  # noqa: E402
from council_os.ledger import LifecycleLedger  # noqa: E402

ORIGIN_MODE_ENV = "CLOUDFLARE_ORIGIN_MODE"
OPEN_MODE = "open"
STRICT_MODE = "strict"
EDGE_HOP_HEADER = "x-avodah-edge"
EDGE_HOP_VALUE = "cloudflare"
HEALTH_PATH = "/health"


def payload_sha256(body: bytes | str | None) -> str:
    if body is None:
        raw = b""
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    else:
        raw = body
    return hashlib.sha256(raw).hexdigest()


def origin_mode(environ: Optional[Mapping[str, str]] = None) -> str:
    env = environ if environ is not None else os.environ
    mode = str(env.get(ORIGIN_MODE_ENV, OPEN_MODE)).strip().lower()
    if mode not in {OPEN_MODE, STRICT_MODE}:
        return OPEN_MODE
    return mode


def parse_edge_headers(headers: Mapping[str, str]) -> Dict[str, Any]:
    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    ray = normalized.get("cf-ray") or ""
    hop = normalized.get(EDGE_HOP_HEADER) or ""
    connecting = normalized.get("cf-connecting-ip") or ""
    via_edge = bool(ray) or hop == EDGE_HOP_VALUE
    return {
        "ray": ray or None,
        "country": normalized.get("cf-ipcountry") or None,
        "visitor": normalized.get("cf-visitor") or None,
        "via_edge": via_edge,
        "has_connecting_ip": bool(connecting),
        "tls": "1.3",
        "payload_hashing": "sha256",
    }


def forbid_direct_origin(path: str, edge: Mapping[str, Any], mode: Optional[str] = None) -> bool:
    current = mode if mode is not None else origin_mode()
    if current != STRICT_MODE:
        return False
    if path == HEALTH_PATH:
        return False
    return not bool(edge.get("via_edge"))


def edge_catalog(enabled: bool = True) -> Dict[str, Any]:
    return {
        "account": EDGE_ACCOUNT,
        "enabled": enabled,
        "left_out": False,
        "virtualized": True,
        "host_decoupled": True,
        "stores_secrets": False,
        "live_login": False,
        "tls": "1.3",
        "products": [dict(item) for item in ENABLED_PRODUCTS],
        "payload_hashing": "sha256",
        "origin_ip_exposed": False,
        "kernel_has_complete_authority": False,
    }


def bind_edge(ledger: Optional[LifecycleLedger] = None) -> CloudflareEdge:
    edge = CloudflareEdge(ledger or LifecycleLedger())
    edge.enable()
    return edge


def refuse_secret_action(action: str) -> None:
    if action in FORBIDDEN_EDGE_ACTIONS or action:
        raise CharterViolation("ZERO_TRUST_ISOLATION")
