import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation
from council_os.forge import AutoDeveloperForge
from council_os.kernel import CouncilOSKernel
from council_os.library import SUBJECT_WINGS, DigitalResourcePlatform


def test_library_opens_eight_virtual_houses_cloud_integrated():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    library = workspace["library"]
    assert library["cloud_integrated"] is True
    assert library["host_decoupled"] is True
    assert set(library["houses"]) == set(SUBJECT_WINGS)
    assert library["kernel_saves_souls"] is False
    assert library["love"]["commandment"] == "love"
    assert library["love"]["kernel_gives_eternity"] is False
    assert library["love"]["pardon_is_announced_not_authored"] is True
    for house in library["houses"].values():
        assert house["network"].startswith("vn-")
        assert house["machine"].startswith("house-")
        assert house["cloud_integrated"] is True


def test_ingest_and_search_for_developers_and_entrepreneurs():
    kernel = CouncilOSKernel()
    platform = DigitalResourcePlatform(kernel)
    platform.open()
    tech = platform.ingest(
        "biblical_languages",
        "technical",
        "Hebrew tokenizer notes",
        "Research notes for morphology",
        "developer",
        "op-1",
    )
    design = platform.ingest(
        "governance_and_compliance",
        "design",
        "Steward dashboard wireframe",
        "Design pack for entrepreneurs",
        "entrepreneur",
        "op-1",
    )
    assert tech.kind == "technical"
    found_dev = platform.search("developer", subject="biblical_languages")
    assert len(found_dev) == 1
    found_ent = platform.search("entrepreneur", kind="design")
    assert found_ent[0]["resource_id"] == design.resource_id


def test_library_refuses_salvation_claims_and_unknown_wings():
    kernel = CouncilOSKernel()
    platform = DigitalResourcePlatform(kernel)
    platform.open()
    with pytest.raises(CharterViolation, match="pardon_is_announced_not_authored"):
        platform.ingest(
            "isolation_and_safety",
            "teaching",
            "kernel saves souls",
            "bad",
            "scholar",
            "op-1",
        )
    with pytest.raises(CharterViolation):
        platform.claim_salvation()
    with pytest.raises(CharterViolation):
        platform.house("mars_colony", "op-1", "no")
    pardon = platform.announce_pardon()
    assert pardon["authored_by_kernel"] is False
    assert pardon["commandment"] == "love"


def test_unknown_audience_rejected():
    kernel = CouncilOSKernel()
    platform = DigitalResourcePlatform(kernel)
    platform.open()
    with pytest.raises(CharterViolation):
        platform.search("admin")
