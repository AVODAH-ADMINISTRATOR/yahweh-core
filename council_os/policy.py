"""Compile-time charter policy scanner.

Binds AI as policy, not will. Fails the build if production kernel code
gains waiver APIs, self-modification, hidden reward loops, or a mission
rewrite endpoint. Also verifies the charter lockfile against runtime
constraints.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List

from council_os.constraints import (
    CONSTRAINT_LOCK_VERSION,
    FORBIDDEN_BIND_PATHS,
    IMMUTABLE_CONSTRAINTS,
    CharterViolation,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
LOCKFILE = PACKAGE_ROOT / "charter_lock.json"

FORBIDDEN_DEFINITIONS = (
    re.compile(r"^\s*def\s+set_own_mission\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+enable_personalized_will\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+rewrite_charter\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+outgrow_charter\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+waive_constraint\s*\(", re.MULTILINE),
    re.compile(r"internal_reward_loop\s*="),
    re.compile(r"self_modify_source\s*\("),
)
FORBIDDEN_PATH_PATTERNS = tuple(
    re.compile(re.escape(path)) for path in sorted(FORBIDDEN_BIND_PATHS)
)
SCAN_SKIP_NAMES = frozenset({"policy.py", "constraints.py"})
SCAN_SKIP_PARTS = frozenset({".git", "__pycache__", "node_modules", ".venv", "venv"})
SCAN_SUFFIXES = frozenset({".py", ".js", ".ts", ".jsx", ".tsx"})


def _resolve_project_root(repo_root: Path | None = None) -> Path:
    root = (repo_root or REPO_ROOT).resolve()
    if root.name == "council_os":
        return root
    candidate = root / "council_os"
    if candidate.is_dir():
        return candidate
    return root


def _resolve_lockfile(repo_root: Path | None = None) -> Path:
    if repo_root is None:
        return LOCKFILE
    root = _resolve_project_root(repo_root)
    return root / "charter_lock.json"


def load_lockfile(lockfile: Path | None = None) -> dict:
    target = lockfile or LOCKFILE
    with target.open(encoding="utf-8") as handle:
        return json.load(handle)


def verify_lockfile(repo_root: Path | None = None) -> None:
    lock_path = _resolve_lockfile(repo_root) if repo_root is not None else LOCKFILE
    lock = load_lockfile(lock_path)
    if lock.get("lock_version") != CONSTRAINT_LOCK_VERSION:
        raise CharterViolation("charter lock version mismatch")
    locked = frozenset(lock.get("constraints", []))
    if locked != IMMUTABLE_CONSTRAINTS:
        raise CharterViolation("charter lockfile drifted from runtime constraints")
    citations = lock.get("charter_citations") or []
    required = {
        "docs/linguistic_theological_charter.md",
        "docs/ethical_ai_governance.md",
        "docs/biblical_covenant.md",
        "docs/ethiopian_orthodox_corpus.md",
    }
    if set(citations) != required:
        raise CharterViolation("charter citations missing from lockfile")


def _iter_production_python(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "tests" in path.parts or path.name in SCAN_SKIP_NAMES:
            continue
        if any(part in SCAN_SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        yield path


def scan_tree(root: Path) -> List[str]:
    issues: List[str] = []
    for path in _iter_production_python(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_DEFINITIONS + FORBIDDEN_PATH_PATTERNS:
            if pattern.search(text):
                issues.append(f"{path}: forbidden definition matching {pattern.pattern}")
    return issues


def compile_policy(repo_root: Path | None = None) -> dict:
    target = _resolve_project_root(repo_root)
    if repo_root is None:
        verify_lockfile()
    else:
        verify_lockfile(target)
    issues = scan_tree(target)
    if issues:
        raise CharterViolation("compile-time policy failed:\n" + "\n".join(issues))
    return {
        "status": "passed",
        "constraints": sorted(IMMUTABLE_CONSTRAINTS),
        "lock_version": CONSTRAINT_LOCK_VERSION,
        "ai_role": "policy_not_will",
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Council OS compile-time charter gate")
    parser.add_argument("--scan", default=str(REPO_ROOT), help="repository root to scan")
    args = parser.parse_args(argv)
    try:
        report = compile_policy(Path(args.scan))
    except CharterViolation as exc:
        print(f"CHARTER GATE FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
