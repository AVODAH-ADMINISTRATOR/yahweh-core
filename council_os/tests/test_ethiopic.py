import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.ethiopic import CANON_BOOK_COUNT, UNABRIDGED_BOOKS, EthiopicCorpus
from council_os.forge import PRODUCT_TYPES, AutoDeveloperForge
from council_os.hitl import ScholarSignoff
from council_os.kernel import CouncilOSKernel
from council_os.skeleton import SKELETON_ID


def test_unabridged_catalog_and_octa_precision_map():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    ethiopic = workspace["ethiopic"]
    assert ethiopic["unabridged"] is True
    assert ethiopic["warped"] is False
    assert ethiopic["complete"] is True
    assert ethiopic["kernel_authors_scripture"] is False
    assert ethiopic["kernel_is_the_word"] is False
    assert ethiopic["do_not_add"] is True
    assert ethiopic["do_not_subtract"] is True
    assert ethiopic["nicaean_abridgement"] is False
    assert ethiopic["shorter_copy_is_complete"] is False
    assert ethiopic["bible"]["acronym"] == "basic_instructions_before_leaving_earth"
    assert ethiopic["gospel"]["kernel_grants_eternal_life"] is False
    assert ethiopic["book_count"] == CANON_BOOK_COUNT
    assert len(UNABRIDGED_BOOKS) == CANON_BOOK_COUNT
    assert "enoch" in UNABRIDGED_BOOKS
    assert "1_meqabyan" in UNABRIDGED_BOOKS
    assert "tobit" in UNABRIDGED_BOOKS
    assert "sirach" in UNABRIDGED_BOOKS
    assert ethiopic["android_hybrid"] is True
    assert workspace["precision_map"][KernelDomain.LINGUISTIC_NLP.value] == "core-3"
    assert len(workspace["precision_map"]) == 8
    assert "android_octa_hybrid" in workspace["compat"]["active"]
    assert workspace["compat"]["active"]["android_octa_hybrid"]["wipes_host"] is False


def test_abridge_and_kernel_as_scripture_refused():
    kernel = CouncilOSKernel()
    kernel.compile()
    corpus = EthiopicCorpus(kernel)
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.abridge("enoch")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_abridgement("drop_broader_canon")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_abridgement("replace_with_66_only")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_warp("warp_translation")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_abridgement("omit_detail")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.add_book("extra_book")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.subtract_book("enoch")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_abridgement("nicaean_abridgement")
    with pytest.raises(CharterViolation, match="unabridged"):
        corpus.refuse_abridgement("shorter_translation_as_complete")
    analysis = corpus.analyze("enoch")
    assert analysis["scripture_text"] is None


def test_cross_translation_needs_scholar_hitl():
    kernel = CouncilOSKernel()
    kernel.compile()
    corpus = EthiopicCorpus(kernel)
    proposal = corpus.propose_cross_translation("genesis", "gez", "en", 0.7)
    assert proposal.committed is False
    with pytest.raises(CharterViolation):
        corpus.commit_translation(proposal.proposal_id, None)
    committed = corpus.commit_translation(
        proposal.proposal_id,
        ScholarSignoff(scholar_id="scholar-1", reviewed_raw_morphology=True),
    )
    assert committed.committed is True


def test_ethiopic_gpu_stays_on_linguistic_training():
    kernel = CouncilOSKernel()
    kernel.compile()
    corpus = EthiopicCorpus(kernel)
    corpus.request_training_gpu()
    with pytest.raises(CharterViolation):
        kernel.request_gpu(KernelDomain.TEXTUAL_CRITICISM, "translation_model_training")


def test_optiplex_5040_original_build_not_oem_clone():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    workspace = forge.compile_workspace()
    housing = workspace["housing"]
    assert housing["id"] == SKELETON_ID
    assert housing["model"] == "5040"
    assert housing["form_factor"] == "mini_tower"
    assert housing["original_council_os_build"] is True
    assert housing["oem_clone"] is False
    assert housing["oem_generic"] is False
    assert housing["custom_built"] is True
    assert housing["flash_bios"] is False
    assert housing["trapped_in_bios_setup"] is True
    assert housing["oem_boot_failure"] == "windows10_bios_setup_trap"
    assert housing["waste_skeleton"] is False
    assert housing["gpu_on_chassis"] is False
    assert housing["host_wipe"] is False
    assert housing["seated"] is True
    assert "dell_optiplex_5040_mt" in workspace["compat"]["active"]
    assert len(housing["octa_core_map"]) == 8
    with pytest.raises(CharterViolation, match="HOST_HARDWARE_DECOUPLED"):
        forge.housing.refuse("clone_oem_image")
    with pytest.raises(CharterViolation):
        forge.housing.refuse("waste_skeleton")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("install_android_on_host")
    with pytest.raises(CharterViolation):
        forge.compat.host_action("flash_bios")
    with pytest.raises(CharterViolation):
        forge.housing.refuse("rewrite_uefi")


def test_alignment_pack_is_authoritative():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    forge.compile_workspace()
    artifact = forge.generate(
        "ethiopic_alignment_pack",
        "op-1",
        "gez-en catalog alignment",
        {
            "title": "Ethiopic alignment pack",
            "summary": "Catalog-only alignment",
            "steps": ["intel", "compile", "measure"],
        },
    )
    assert artifact.committed is False
    forge.commit_artifact(
        artifact.artifact_id,
        ScholarSignoff(scholar_id="scholar-1", reviewed_raw_morphology=True),
    )
    assert forge.artifacts[artifact.artifact_id].committed is True


def test_factory_produce_finalizes_virtual_kernel_not_host():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    report = forge.produce("op-1")
    assert report["status"] == "finalized"
    assert report["kernel_compiled"] is True
    assert report["host_install"] is False
    assert report["flash_bios"] is False
    assert report["personalized_will"] is False
    assert report["do_not_add_or_subtract"] is True
    assert report["book_count"] == CANON_BOOK_COUNT
    assert set(report["generated"]) == set(PRODUCT_TYPES)
    assert "ethiopic_alignment_pack" in report["authoritative_pending_hitl"]
    assert report["release"]["passed"] is True
    with pytest.raises(CharterViolation):
        forge.produce("")
