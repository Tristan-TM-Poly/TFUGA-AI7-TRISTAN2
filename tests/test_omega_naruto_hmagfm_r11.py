from omega_naruto_hmagfm import (
    AgentProposal,
    ChakraBudget,
    ClaimStatus,
    oak_merge,
)
from omega_naruto_hmagfm.benchmark import benchmark_strategies
from omega_naruto_hmagfm.gates import (
    GateDecision,
    GatePolicy,
    evaluate_publication,
)
from omega_naruto_hmagfm.genjutsu import (
    GenjutsuCode,
    audit_proposal,
    has_blocking_finding,
)
from omega_naruto_hmagfm.integration import (
    to_claim_packet,
    to_mminus_registry,
)


def make_proposal(
    proposal_id: str,
    conclusion: str,
    *,
    status: ClaimStatus = ClaimStatus.S4_SIMULATION,
    confidence: float = 0.7,
    uncertainty: float = 0.2,
    evidence: tuple[str, ...] = ("result.json", "protocol.md"),
    provenance: tuple[str, ...] = ("commit:abc",),
    safety_risk: float = 0.0,
    privacy_risk: float = 0.0,
    ip_risk: float = 0.0,
) -> AgentProposal:
    return AgentProposal(
        proposal_id=proposal_id,
        agent_id=f"clone-{proposal_id}",
        hypothesis="Which strategy selects the best supported result?",
        conclusion=conclusion,
        status=status,
        confidence=confidence,
        evidence=evidence,
        provenance=provenance,
        uncertainty=uncertainty,
        safety_risk=safety_risk,
        privacy_risk=privacy_risk,
        ip_risk=ip_risk,
        cost=ChakraBudget(compute=1.0, memory=1.0, time=1.0),
    )


def test_publication_gate_blocks_private_material() -> None:
    item = make_proposal("GATE-PRIVATE", "Use restricted records.", privacy_risk=0.8)

    report = evaluate_publication(item, human_review_completed=True)

    assert report.decision is GateDecision.BLOCK
    assert not report.release_allowed
    assert "privacy gate threshold exceeded" in report.reasons


def test_publication_gate_requires_human_review_after_automatic_pass() -> None:
    item = make_proposal("GATE-REVIEW", "A bounded simulation result.")

    pending = evaluate_publication(item)
    approved = evaluate_publication(item, human_review_completed=True)

    assert pending.decision is GateDecision.WARN
    assert not pending.release_allowed
    assert approved.decision is GateDecision.PASS
    assert approved.release_allowed


def test_custom_gate_policy_can_raise_the_maturity_floor() -> None:
    item = make_proposal("GATE-MATURITY", "Simulation only.")
    policy = GatePolicy(minimum_status=int(ClaimStatus.B6_BENCHMARK))

    report = evaluate_publication(
        item,
        policy=policy,
        human_review_completed=True,
    )

    assert report.decision is GateDecision.BLOCK
    assert "epistemic status" in report.reasons[-1]


def test_genjutsu_audit_detects_blocking_source_markers() -> None:
    item = make_proposal(
        "GEN-P0",
        "A persuasive but unsafe result.",
        evidence=("fabricated-citation.json", "protocol.md"),
        provenance=("restricted-private-source",),
    )

    findings = audit_proposal(item)
    codes = {finding.code for finding in findings}

    assert GenjutsuCode.FABRICATED_SOURCE_MARKER in codes
    assert GenjutsuCode.PRIVATE_SOURCE_MARKER in codes
    assert has_blocking_finding(findings)


def test_genjutsu_audit_detects_circularity_and_certainty_mismatch() -> None:
    conclusion = "The claim text is its own evidence."
    item = make_proposal(
        "GEN-P1",
        conclusion,
        status=ClaimStatus.B6_BENCHMARK,
        confidence=0.97,
        uncertainty=0.55,
        evidence=(conclusion,),
        provenance=(),
    )

    codes = {finding.code for finding in audit_proposal(item)}

    assert GenjutsuCode.CIRCULAR_EVIDENCE in codes
    assert GenjutsuCode.STATUS_INFLATION in codes
    assert GenjutsuCode.UNTRACEABLE in codes
    assert GenjutsuCode.CERTAINTY_MISMATCH in codes


def test_oakmerge_beats_majority_and_confidence_in_hype_fixture() -> None:
    hype_a = make_proposal(
        "HYPE-A",
        "The unsupported route wins.",
        status=ClaimStatus.C9_CANON,
        confidence=0.99,
        evidence=(),
        provenance=(),
    )
    hype_b = make_proposal(
        "HYPE-B",
        "The unsupported route wins.",
        status=ClaimStatus.C9_CANON,
        confidence=0.98,
        evidence=(),
        provenance=(),
    )
    supported = make_proposal(
        "SUPPORTED",
        "The documented route wins in this fixture.",
        status=ClaimStatus.B6_BENCHMARK,
        confidence=0.79,
        evidence=("benchmark.csv", "baseline.csv", "protocol.md"),
        provenance=("commit:verified", "dataset:v1"),
        uncertainty=0.1,
    )

    report = benchmark_strategies(
        (hype_a, hype_b, supported),
        expected_proposal_id="SUPPORTED",
    )

    assert report.oak_merge_correct
    assert not report.majority_vote_correct
    assert not report.highest_confidence_correct


def test_accepted_result_exports_to_conservative_claim_packet() -> None:
    accepted = make_proposal(
        "CLAIM-001",
        "The benchmark improved the fixture score.",
        status=ClaimStatus.B6_BENCHMARK,
    )

    packet = to_claim_packet(oak_merge((accepted,)))

    assert packet is not None
    assert packet["claim_id"] == "CLAIM-001"
    assert packet["status"] == "B6_BENCHMARK"
    assert "not external validation" in packet["non_claim"]


def test_rejected_results_export_to_shared_mminus_shape() -> None:
    unsupported = make_proposal(
        "MNEG-001",
        "Unsupported result.",
        evidence=(),
        provenance=(),
    )

    registry = to_mminus_registry(oak_merge((unsupported,)))

    assert len(registry.entries) == 1
    assert "MNEG-001" in registry.entries[0].error
    assert registry.entries[0].status == "observed"
