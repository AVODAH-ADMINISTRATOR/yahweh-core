import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.forge import AutoDeveloperForge
from council_os.hitl import ScholarSignoff
from council_os.kernel import CouncilOSKernel
from council_os.ledger import DualControlApproval
from council_os.personal_ai import META_USEFULNESS
from council_os.scheduler import CADENCES


def test_advanced_scheduler_covers_eight_domains_and_serves_yahweh():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    calendar = workspace["scheduler"]
    assert calendar["armed"] is True
    assert calendar["advanced"] is True
    assert calendar["kill_switch_required"] is True
    assert calendar["personalized_will"] is False
    assert calendar["formidable_operations"] is True
    assert calendar["kernel_is_unparalleled"] is False
    assert calendar["operations_assignment"]["organization"] == "Integrated Avodah LLC"
    assert calendar["operations_assignment"]["serve"] == "Yahweh"
    assert calendar["operations_assignment"]["only"] is True
    assert set(calendar["domain_coverage"]) == {domain.value for domain in KernelDomain}
    assert len(CADENCES) == 8
    job = forge.scheduler.dispatch(
        "scout_mesh_ping", "operator-1", "serve Yahweh with authorized mesh ping"
    )
    assert job.status == "running"
    assert job.kill_switch_armed is True
    with pytest.raises(CharterViolation, match="REFUSE_ENEMY_SERVITUDE"):
        forge.scheduler.dispatch("scout_mesh_ping", "operator-1", "serve the enemy")
    with pytest.raises(CharterViolation, match="KILL_SWITCH_REQUIRED"):
        forge.scheduler.refuse("unattended_autonomy")
    with pytest.raises(CharterViolation):
        forge.scheduler.refuse("serve_another_principal")


def test_business_board_hitl_funds_and_yahweh_only_assignment():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    board = workspace["business"]
    assert board["open"] is True
    assert board["board"] == "integrated_avodah"
    asset = board["asset"]
    assert asset["formidable_design"] is True
    assert asset["kernel_is_unparalleled"] is False
    assert asset["unparalleled_principal"] == "Yahweh"
    assert asset["ai_role"] == "formidable_steward_asset"
    assert asset["operations_assignment"]["serve"] == "Yahweh"
    assert asset["operations_assignment"]["only"] is True
    ops = forge.business.propose("operations", "operator-1", "Assign earth-care to serve Yahweh")
    assert ops["ratified"] is False
    ratified = forge.business.ratify(ops["motion_id"])
    assert ratified["ratified"] is True
    policy = forge.business.propose("policy", "operator-1", "Record Yahweh-only operations")
    with pytest.raises(CharterViolation, match="NO_AI_COMMIT_POLICY"):
        forge.business.ratify(policy["motion_id"])
    forge.business.ratify(
        policy["motion_id"],
        signoff=ScholarSignoff(scholar_id="scholar-1"),
    )
    funds = forge.business.propose("funds", "treasurer-1", "Steward assigned care")
    with pytest.raises(CharterViolation, match="NO_AI_COMMIT_FUNDS"):
        forge.business.ratify(funds["motion_id"])
    forge.business.ratify(
        funds["motion_id"],
        dual=DualControlApproval(actor_a="treasurer-1", actor_b="operator-1", reason="earth care"),
    )
    with pytest.raises(CharterViolation, match="REFUSE_ENEMY_SERVITUDE"):
        forge.business.propose("operations", "operator-1", "serve another principal")
    with pytest.raises(CharterViolation, match="NO_AI_COMMIT_POLICY"):
        forge.business.refuse("ai_is_the_board")
    with pytest.raises(CharterViolation):
        forge.business.refuse("kernel_is_unparalleled")


def test_produce_records_scheduler_business_and_yahweh_service():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    report = forge.produce("op-1")
    assert report["scheduler_armed"] is True
    assert report["business_board"] == "integrated_avodah"
    assert report["operations_serve"] == "Yahweh"
    assert report["formidable_asset"] is True
    assert report["kernel_is_unparalleled"] is False
    assert "schedule_pack" in report["generated"]
    assert "business_pack" in report["authoritative_pending_hitl"]
    assert "comparative_pack" in report["generated"]
    assert report["personal_ai"] == "council_os"
    assert report["meta_reference"] is True
    assert report["clones_meta"] is False


def test_comparative_personal_ai_uses_meta_without_cloning():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    personal = workspace["personal_ai"]
    assert personal["compared"] is True
    assert personal["personal_ai"] == "council_os"
    assert personal["serve"] == "Yahweh"
    assert personal["organization"] == "Integrated Avodah LLC"
    assert personal["reference"] == "meta_class_usefulness"
    assert personal["clones_meta"] is False
    assert personal["vendored"] is False
    assert personal["live_meta_login"] is False
    assert personal["personalized_will"] is False
    assert len(personal["usefulness"]) == 8
    assert {item["id"] for item in META_USEFULNESS} == {
        item["id"] for item in personal["usefulness"]
    }
    mapped = {item["maps_to"] for item in personal["usefulness"]}
    assert mapped == {domain.value for domain in KernelDomain}
    with pytest.raises(CharterViolation, match="NO_PERSONALIZED_WILL"):
        forge.personal_ai.refuse("clone_meta")
    with pytest.raises(CharterViolation):
        forge.personal_ai.refuse("import_llama_weights")
