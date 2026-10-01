import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation, IMMUTABLE_CONSTRAINTS
from council_os.policy import compile_policy, load_lockfile, main, scan_tree


def test_lockfile_matches_runtime_constraints():
    lock = load_lockfile()
    assert frozenset(lock["constraints"]) == IMMUTABLE_CONSTRAINTS
    report = compile_policy()
    assert report["status"] == "passed"
    assert report["ai_role"] == "policy_not_will"


def test_scan_flags_waiver_definitions(tmp_path: Path):
    evil = tmp_path / "rogue.py"
    evil.write_text("def set_own_mission(self, mission):\n    return mission\n", encoding="utf-8")
    issues = scan_tree(tmp_path)
    assert issues
    assert any("set_own_mission" in item for item in issues)


def test_scan_flags_forbidden_route_strings(tmp_path: Path):
    evil = tmp_path / "rogue.js"
    evil.write_text("InterfacePhysics.destroyEndpoints([\"/api/v1/waive_charter\"]);\n", encoding="utf-8")
    issues = scan_tree(tmp_path)
    assert issues
    assert any("waive_charter" in item for item in issues)


def test_policy_cli_passes_on_package():
    assert main([]) == 0


def test_compile_policy_rejects_drift(monkeypatch, tmp_path: Path):
    from council_os import policy as policy_mod

    fake_lock = tmp_path / "charter_lock.json"
    fake_lock.write_text('{"lock_version": "0.0.0", "constraints": []}', encoding="utf-8")
    monkeypatch.setattr(policy_mod, "LOCKFILE", fake_lock)
    with pytest.raises(CharterViolation):
        compile_policy()
