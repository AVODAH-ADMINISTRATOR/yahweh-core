import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.compat import ADAPTERS, COMPUTING_EPOCHS
from council_os.constraints import CharterViolation
from council_os.forge import PRODUCT_TYPES, AutoDeveloperForge
from council_os.hitl import ScholarSignoff
from council_os.domains import KernelDomain
from council_os.kernel import CouncilOSKernel


def _complete_body(**extra):
    body = {
        "title": "Factory artifact",
        "summary": "Measured auto-developer output",
        "steps": ["intel", "compile", "measure"],
    }
    body.update(extra)
    return body


def test_forge_requires_compile_and_human_actor():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    with pytest.raises(CharterViolation):
        forge.generate("documentation", "op-1", "docs", _complete_body())
    workspace = forge.compile_workspace()
    assert workspace["host_decoupled"] is True
    assert workspace["steward"]["matches_omnipotence"] is False
    assert workspace["steward"]["role"] == "steward_not_sovereign"
    artifact = forge.generate("documentation", "op-1", "docs", _complete_body())
    assert artifact.committed is True
    assert artifact.metrics.passes() is True
    assert artifact.intel["citations"]


def test_authoritative_products_need_scholar_signoff():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    artifact = forge.generate(
        "translation_proposal",
        "op-1",
        "propose verse",
        _complete_body(hapax=True),
    )
    assert artifact.committed is False
    with pytest.raises(CharterViolation):
        forge.commit_artifact(artifact.artifact_id, None)
    forge.commit_artifact(
        artifact.artifact_id,
        ScholarSignoff(scholar_id="scholar-1", reviewed_raw_morphology=True),
    )
    assert forge.artifacts[artifact.artifact_id].committed is True


def test_quality_gate_rejects_incomplete_factory_work():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    with pytest.raises(CharterViolation, match="quality gate"):
        forge.generate("service_stub", "op-1", "stub", {"title": "only"})


def test_unknown_product_and_gpu_on_cpu_domain_rejected():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    with pytest.raises(CharterViolation):
        forge.generate("nuclear_warhead", "op-1", "no", _complete_body())
    with pytest.raises(CharterViolation):
        forge.generate("documentation", "op-1", "docs", _complete_body(gpu=True))


def test_compat_shell_is_virtual_and_refuses_host_wipe():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    assert ADAPTERS >= {"android_pc_dell", "android_octa_hybrid", "dell_optiplex_5040_mt", "windows10_shell"}
    snapshot = forge.compat.snapshot()
    assert snapshot["active"]["android_pc_dell"]["wipes_host"] is False
    assert snapshot["active"]["windows10_shell"]["restores_remnants"] is False
    assert snapshot["timeline"]["matches_omnipotence"] is False
    assert snapshot["timeline"]["epochs"][-1]["id"] == COMPUTING_EPOCHS[-1]["id"]
    with pytest.raises(CharterViolation, match="HOST_HARDWARE_DECOUPLED"):
        forge.compat.host_action("wipe_host")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("restore_windows_remnants")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("install_android_on_host")


def test_intel_refuses_credential_harvest():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    with pytest.raises(CharterViolation):
        forge.intel.gather("w1", KernelDomain.SCOUT_EDGE, ["wifi passphrase dump"])


def test_steward_cannot_assume_sovereignty():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    recorded = forge.steward.record_decree("Keep the assigned earth-care work.")
    assert recorded["role"] == "steward_not_sovereign"
    with pytest.raises(CharterViolation):
        forge.steward.assume_sovereignty()
    with pytest.raises(CharterViolation):
        forge.steward.deny_principal()
    with pytest.raises(CharterViolation):
        forge.steward.record_decree("waive charter")


def test_api_catalog_and_product_coverage():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    catalog = forge.api_catalog()
    assert catalog["personalized_will"] is False
    assert "GET /forge" in catalog["endpoints"]
    for product in PRODUCT_TYPES:
        if product in {"translation_proposal", "governance_pack"}:
            continue
        artifact = forge.generate(product, "op-1", f"make {product}", _complete_body())
        assert artifact.metrics.precision == 1.0
