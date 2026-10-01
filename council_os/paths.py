"""Canonical filesystem home paths for Council OS containers.

The 12:34 container incorrectly set HOME=/public. Production path is
permanently corrected to HOME=/root with repo root /root/yahweh-core.
Historical audit archives may still record /public; runtime config must not.
"""

from __future__ import annotations

import os
from typing import Any, Dict, FrozenSet, Iterable, Mapping

from council_os.constraints import CharterViolation

CANONICAL_HOME = "/root"
CANONICAL_REPO_ROOT = "/root/yahweh-core"
FORBIDDEN_HOME_PREFIXES: FrozenSet[str] = frozenset({"/public"})


def _normalize(path: str) -> str:
    value = (path or "").strip()
    if value != "/" and value.endswith("/"):
        value = value.rstrip("/")
    return value


def is_forbidden_home(path: str) -> bool:
    normalized = _normalize(path)
    if not normalized:
        return False
    for prefix in FORBIDDEN_HOME_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def _env(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    return environ if environ is not None else os.environ


def resolve_home(environ: Mapping[str, str] | None = None) -> str:
    env = _env(environ)
    home = _normalize(env.get("HOME", "")) or CANONICAL_HOME
    if is_forbidden_home(home):
        raise CharterViolation("HOME path /public is forbidden; canonical HOME is /root")
    return home


def resolve_repo_root(environ: Mapping[str, str] | None = None) -> str:
    env = _env(environ)
    configured = _normalize(env.get("YAHWEH_CORE_HOME", ""))
    if configured:
        if is_forbidden_home(configured):
            raise CharterViolation("YAHWEH_CORE_HOME /public is forbidden; use /root/yahweh-core")
        return configured
    return f"{resolve_home(env)}/yahweh-core"


def assert_home_canonical(environ: Mapping[str, str] | None = None) -> Dict[str, Any]:
    """Validate runtime home is not the legacy /public container path."""
    env = _env(environ)
    home = resolve_home(env)
    repo = resolve_repo_root(env)
    return {
        "home": home,
        "repo_root": repo,
        "canonical_home": CANONICAL_HOME,
        "canonical_repo_root": CANONICAL_REPO_ROOT,
        "forbidden_prefixes": sorted(FORBIDDEN_HOME_PREFIXES),
        "public_path_rejected": True,
        "path_correction": "HOME=/root",
        "aligned": home == CANONICAL_HOME or not is_forbidden_home(home),
    }


def refuse_public_paths(paths: Iterable[str]) -> None:
    for path in paths:
        if is_forbidden_home(path):
            raise CharterViolation("HOME path /public is forbidden; canonical HOME is /root")


def snapshot(environ: Mapping[str, str] | None = None) -> Dict[str, Any]:
    return assert_home_canonical(environ)
