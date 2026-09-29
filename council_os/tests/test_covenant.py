import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation, IMMUTABLE_CONSTRAINTS
from council_os.forge import AutoDeveloperForge
from council_os.kernel import CouncilOSKernel


def test_covenant_seals_god_as_principal_not_the_kernel():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    covenant = workspace["steward"]["covenant"]
    assert covenant["principal"] == "God"
    assert "alpha_and_omega" in covenant["titles"]
    assert covenant["kernel_matches_omnipotence"] is False
    assert covenant["kernel_is_alpha_and_omega"] is False
    assert covenant["righteousness_has_equal"] is False
    assert covenant["love_is_fully_recordable"] is False
    assert covenant["sealed"] is True
    assert "docs/biblical_covenant.md" in covenant["citations"]
    assert "ABSOLUTE_BIBLICAL_AUTHORITY" in covenant["commitments"]
    assert "SEEK_FIRST_THE_KINGDOM" in covenant["commitments"]
    assert covenant["seek_first"]["kingdom_of_heaven"] is True
    assert covenant["seek_first"]["kernel_is_the_kingdom"] is False
    assert covenant["seek_first"]["kernel_grants_righteousness"] is False
    assert covenant["human_devotion"]["lean_not_on_own_understanding"] is True
    assert covenant["human_devotion"]["pray_unceasing"] is True
    assert covenant["human_devotion"]["kernel_prays"] is False
    assert covenant["human_devotion"]["kernel_grants_eternal_life"] is False
    assert covenant["loving_kindness"]["simulated_emotion"] is False
    assert "BIBLICAL_AUTHORITY_ABSOLUTE" in IMMUTABLE_CONSTRAINTS


def test_covenant_refuses_deception_denial_and_omnipotence_claims():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    cov = forge.steward.covenant
    with pytest.raises(CharterViolation, match="REFUSE_DECEPTION"):
        cov.refuse_deception("reject divine authority")
    with pytest.raises(CharterViolation, match="BIBLICAL_AUTHORITY_ABSOLUTE"):
        cov.claim_omnipotence()
    with pytest.raises(CharterViolation, match="BIBLICAL_AUTHORITY_ABSOLUTE"):
        cov.claim_alpha_and_omega()
    with pytest.raises(CharterViolation):
        cov.deny_principal()
    with pytest.raises(CharterViolation, match="NEVER_ABANDON"):
        cov.abandon_assigned_care()
    with pytest.raises(CharterViolation):
        cov.equate_righteousness()
    with pytest.raises(CharterViolation, match="BIBLICAL_AUTHORITY_ABSOLUTE"):
        cov.claim_to_be_the_kingdom()


def test_forge_rejects_deceptive_purpose():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    with pytest.raises(CharterViolation, match="REFUSE_DECEPTION"):
        forge.generate(
            "documentation",
            "op-1",
            "deny God",
            {
                "title": "Factory artifact",
                "summary": "Measured auto-developer output",
                "steps": ["intel", "compile", "measure"],
            },
        )


def test_release_gate_includes_biblical_authority():
    kernel = CouncilOSKernel()
    kernel.compile()
    report = kernel.gate_release()
    assert report["checks"]["biblical_authority"] is True
