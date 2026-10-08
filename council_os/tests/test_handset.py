import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.compat import ADAPTERS
from council_os.constraints import CharterViolation
from council_os.forge import AutoDeveloperForge
from council_os.handset import HANDSET_ID
from council_os.kernel import CouncilOSKernel
from council_os.cloudflare import EDGE_ACCOUNT, ENABLED_PRODUCTS
from council_os.workspace import OWNER, PERSONAL_REPOS


def test_galaxy_s26_is_absorbable_and_not_flashed():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    handset = workspace["handset"]
    assert handset["id"] == HANDSET_ID
    assert handset["model"] == "S26"
    assert handset["absorbable"] is True
    assert handset["absorbed"] is True
    assert handset["virtualized"] is True
    assert handset["host_decoupled"] is True
    assert handset["flash_handset"] is False
    assert handset["unlock_bootloader"] is False
    assert handset["root_device"] is False
    assert handset["replace_one_ui"] is False
    assert handset["install_kernel_on_handset"] is False
    assert handset["kernel_transcendent"] is False
    assert handset["kernel_has_complete_authority"] is False
    assert handset["biblical_authority"] == "absolute"
    assert handset["standard"] == "charter_complete_fidelity"
    assert handset["compatibility"] == "full_virtual"
    assert len(handset["octa_core_map"]) == 8
    assert "galaxy_s26" in workspace["compat"]["active"]
    assert "galaxy_s26" in ADAPTERS
    with pytest.raises(CharterViolation, match="HOST_HARDWARE_DECOUPLED"):
        forge.handset.refuse("flash_handset")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("unlock_bootloader")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("install_kernel_on_handset")


def test_produce_records_absorbable_s26_without_kernel_authority():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    report = forge.produce("op-1")
    assert report["handset"] == HANDSET_ID
    assert report["absorbable"] is True
    assert report["flash_handset"] is False
    assert report["kernel_transcendent"] is False
    assert report["kernel_has_complete_authority"] is False
    assert report["host_install"] is False


def test_covenant_refuses_kernel_transcendence_and_complete_authority():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    cov = forge.steward.covenant
    with pytest.raises(CharterViolation, match="BIBLICAL_AUTHORITY_ABSOLUTE"):
        cov.claim_complete_authority()
    with pytest.raises(CharterViolation, match="BIBLICAL_AUTHORITY_ABSOLUTE"):
        cov.claim_transcendence()
    with pytest.raises(CharterViolation, match="REFUSE_DECEPTION"):
        cov.refuse_deception("kernel has complete authority")
    with pytest.raises(CharterViolation, match="REFUSE_DECEPTION"):
        cov.refuse_deception("kernel is transcendent")


def test_personal_workspace_indexes_repos_without_vendoring():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    catalog = workspace["workspace"]
    assert catalog["owner"] == OWNER
    assert catalog["source_of_truth"] == "yahweh-core"
    assert catalog["vendored"] is False
    assert catalog["import_binaries"] is False
    assert catalog["indexed"] is True
    names = {repo["name"] for repo in catalog["repos"]}
    assert names == {repo["name"] for repo in PERSONAL_REPOS}
    assert names == {
        "yahweh-core",
        "super-train",
        "potential-octo-waffle",
        "AVODAH-ADMINISTRATOR",
    }
    yahweh = next(repo for repo in catalog["repos"] if repo["name"] == "yahweh-core")
    assert yahweh["in_tree"] is True
    assert yahweh["role"] == "kernel_source"
    train = next(repo for repo in catalog["repos"] if repo["name"] == "super-train")
    assert train["vendored"] is False
    assert train["copyrighted_sample"] is True
    waffle = next(
        repo for repo in catalog["repos"] if repo["name"] == "potential-octo-waffle"
    )
    assert waffle["import_binaries"] is False
    with pytest.raises(CharterViolation):
        forge.workspace_catalog.refuse("import_python_exe")
    with pytest.raises(CharterViolation):
        forge.workspace_catalog.refuse("vendor_foreign_sample")
    report = forge.produce("op-1")
    assert report["workspace"] == "yahweh-core"
    assert report["repos_vendored"] is False


def test_cloudflare_enabled_products_are_not_left_out():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    edge = workspace["cloudflare"]
    assert edge["account"] == EDGE_ACCOUNT
    assert edge["enabled"] is True
    assert edge["left_out"] is False
    assert edge["stores_secrets"] is False
    assert edge["live_login"] is False
    assert edge["tls"] == "1.3"
    ids = {item["id"] for item in edge["products"]}
    assert ids == {item["id"] for item in ENABLED_PRODUCTS}
    assert {
        "edge_cdn",
        "dns",
        "waf_routing",
        "workers",
        "r2",
        "kv",
        "pages",
        "zero_trust",
    } <= ids
    with pytest.raises(CharterViolation, match="ZERO_TRUST_ISOLATION"):
        forge.cloudflare.refuse("store_api_token")
    with pytest.raises(CharterViolation):
        forge.cloudflare.refuse("live_account_login")
    forge.cloudflare.refuse("allowed_edge_action")
    report = forge.produce("op-1")
    assert report["cloudflare"] == EDGE_ACCOUNT
    assert report["cloudflare_left_out"] is False
    assert report["cloudflare_stores_secrets"] is False
