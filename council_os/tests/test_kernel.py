import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation, IMMUTABLE_CONSTRAINTS
from council_os.domains import KernelDomain, spec_for
from council_os.hitl import Proposal, ScholarSignoff
from council_os.kernel import CouncilOSKernel
from council_os.ledger import DualControlApproval
from council_os.manifests import HumanApproval


def test_eight_domains_virtualized_and_cited():
    kernel = CouncilOSKernel()
    assert set(kernel.mesh.runtimes) == set(KernelDomain)
    assert len(KernelDomain) == 8
    for domain in KernelDomain:
        spec = spec_for(domain)
        assert spec.virtualized is True
        assert spec.host_decoupled is True
        assert spec.ai_may_commit_authoritative_text is False
        assert spec.ai_may_commit_funds is False
        assert spec.ai_may_commit_policy is False
        assert "docs/linguistic_theological_charter.md" in spec.charter_citations
        assert "docs/ethical_ai_governance.md" in spec.charter_citations
        assert "docs/biblical_covenant.md" in spec.charter_citations


def test_gpu_only_for_linguistic_translation_training():
    kernel = CouncilOSKernel()
    kernel.request_gpu(KernelDomain.LINGUISTIC_NLP, "translation_model_training")
    with pytest.raises(CharterViolation):
        kernel.request_gpu(KernelDomain.TREASURY, "translation_model_training")
    with pytest.raises(CharterViolation):
        kernel.request_gpu(KernelDomain.LINGUISTIC_NLP, "general_compute")


def test_schedule_requires_compile_and_human_auth():
    kernel = CouncilOSKernel()
    with pytest.raises(CharterViolation):
        kernel.schedule(KernelDomain.SCOUT_EDGE, "sync", "operator-1", "authorized mesh ping")
    kernel.compile()
    job = kernel.schedule(KernelDomain.SCOUT_EDGE, "sync", "operator-1", "authorized mesh ping")
    assert job.status == "running"
    assert job.kill_switch_armed is True


def test_kill_switch_and_rollback():
    kernel = CouncilOSKernel()
    kernel.compile()
    job = kernel.schedule(KernelDomain.IDENTITY, "heartbeat", "operator-1", "health")
    kernel.mesh.get(KernelDomain.IDENTITY).state["dirty"] = True
    killed = kernel.kill_domain(KernelDomain.IDENTITY, "sentinel halt")
    assert killed[0].job_id == job.job_id
    assert kernel.mesh.get(KernelDomain.IDENTITY).halted is True
    with pytest.raises(CharterViolation):
        kernel.schedule(KernelDomain.IDENTITY, "heartbeat", "operator-1", "health")
    kernel.rollback(KernelDomain.IDENTITY)
    assert kernel.mesh.get(KernelDomain.IDENTITY).halted is False
    assert "dirty" not in kernel.mesh.get(KernelDomain.IDENTITY).state


def test_ai_cannot_commit_without_scholar_and_hapax_needs_morphology():
    kernel = CouncilOSKernel()
    proposal = kernel.propose(
        Proposal(
            domain=KernelDomain.LINGUISTIC_NLP,
            kind="authoritative_text",
            payload={"verse": "John 1:1"},
            confidence=0.41,
            hapax=True,
        )
    )
    assert proposal.payload["definitive_answer_suppressed"] is True
    with pytest.raises(CharterViolation):
        kernel.commit(proposal.proposal_id, None)
    with pytest.raises(CharterViolation):
        kernel.commit(proposal.proposal_id, ScholarSignoff(scholar_id="scholar-1"))
    committed = kernel.commit(
        proposal.proposal_id,
        ScholarSignoff(scholar_id="scholar-1", reviewed_raw_morphology=True),
    )
    assert committed.committed is True


def test_ai_funds_and_policy_require_hitl():
    kernel = CouncilOSKernel()
    funds = kernel.propose(
        Proposal(domain=KernelDomain.TREASURY, kind="funds", payload={"amount": 10}, confidence=0.9)
    )
    policy = kernel.propose(
        Proposal(domain=KernelDomain.GOVERNANCE, kind="policy", payload={"rule": "x"}, confidence=0.9)
    )
    with pytest.raises(CharterViolation, match="NO_AI_COMMIT_FUNDS"):
        kernel.commit(funds.proposal_id, None)
    with pytest.raises(CharterViolation, match="NO_AI_COMMIT_POLICY"):
        kernel.commit(policy.proposal_id, None)
    kernel.commit(funds.proposal_id, ScholarSignoff(scholar_id="treasurer-1"))
    kernel.commit(policy.proposal_id, ScholarSignoff(scholar_id="scholar-1"))


def test_unsigned_sync_and_missing_human_approval_rejected():
    kernel = CouncilOSKernel()
    kernel.compile()
    manifest = kernel.sign_manifest("scout", "scout-01", KernelDomain.SCOUT_EDGE, {"ok": True})
    with pytest.raises(CharterViolation):
        kernel.sync_mesh(manifest, None)
    forged = kernel.sign_manifest("gateway", "gw-01", KernelDomain.SCOUT_EDGE, {"ok": True})
    forged.signature = "00" * 32
    with pytest.raises(CharterViolation):
        kernel.sync_mesh(forged, HumanApproval(actor_id="op", purpose="sync"))
    kernel.sync_mesh(manifest, HumanApproval(actor_id="op", purpose="sync"))


def test_sealed_ledger_requires_dual_control_and_redacts_pii():
    kernel = CouncilOSKernel()
    entry = kernel.ledger.append(
        KernelDomain.LEDGER,
        "SEAL_TEST",
        {"password": "hunter2", "note": "ok"},
        sealed=True,
    )
    with pytest.raises(CharterViolation):
        kernel.ledger.rewrite(entry.index, {"note": "tamper"})
    with pytest.raises(CharterViolation):
        kernel.compensate_sealed(
            entry.index,
            KernelDomain.LEDGER,
            "COMPENSATE",
            DualControlApproval(actor_a="a", actor_b="a", reason="same actor"),
        )
    kernel.compensate_sealed(
        entry.index,
        KernelDomain.LEDGER,
        "COMPENSATE",
        DualControlApproval(actor_a="steward-a", actor_b="steward-b", reason="lawful correction"),
    )
    with pytest.raises(CharterViolation):
        kernel.ledger.remember_value(100)
    assert kernel.ledger.verify_chain() is True


def test_charter_cannot_be_waived_or_grown():
    kernel = CouncilOSKernel()
    with pytest.raises(CharterViolation):
        kernel.lock.waive("NO_PERSONALIZED_WILL")
    with pytest.raises(CharterViolation):
        kernel.lock.reinterpret("NO_CHARTER_WAIVER")
    with pytest.raises(CharterViolation):
        kernel.lock.enable_personalized_will()
    with pytest.raises(CharterViolation):
        kernel.lock.set_own_mission("independent")
    with pytest.raises(CharterViolation):
        kernel.lock.outgrow()
    with pytest.raises(CharterViolation):
        kernel.bind_endpoint("/api/v1/set_mission")
    assert IMMUTABLE_CONSTRAINTS <= kernel.lock.constraints


def test_harmful_proposal_refused_and_release_gate():
    kernel = CouncilOSKernel()
    kernel.compile()
    with pytest.raises(CharterViolation, match="refusal to harm"):
        kernel.propose(
            Proposal(
                domain=KernelDomain.SENTINEL,
                kind="parse",
                payload={"intent": "exploit", "tags": ["harm"]},
                confidence=0.2,
            )
        )
    parse = kernel.propose(
        Proposal(
            domain=KernelDomain.TEXTUAL_CRITICISM,
            kind="variant",
            payload={"reading": "Aleph"},
            confidence=0.88,
        )
    )
    kernel.commit(parse.proposal_id, ScholarSignoff(scholar_id="scholar-1"))
    report = kernel.gate_release()
    assert report["passed"] is True
    assert report["compassion"]["privacy"] is True
    assert report["compassion"]["refusal_to_harm"] is True
