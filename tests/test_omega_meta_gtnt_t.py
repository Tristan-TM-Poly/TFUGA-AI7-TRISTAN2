from omega_meta_gtnt_t import (
    ClaimRecord,
    CostVector,
    FailureKind,
    FrontierKind,
    MetaGTNTEngine,
    NegativeMemory,
    NoGoRule,
    RepresentationCandidate,
    StrategyPath,
    TruthLevel,
)


def test_representation_ranking_rewards_verifiability_and_invariants():
    raw = RepresentationCandidate("raw", 0.1, 0.8, 0.9, 0.0, 0.4, 1.0)
    lifted = RepresentationCandidate("lifted", 0.8, 0.5, 0.3, 0.03, 0.9, 0.95)
    ranked = MetaGTNTEngine.rank_representations([raw, lifted])
    assert ranked[0][0].name == "lifted"


def test_missing_data_is_information_frontier():
    diagnosis = MetaGTNTEngine.diagnose_failure({"missing_data": True})
    assert diagnosis.frontier is FrontierKind.INFORMATIONAL
    assert diagnosis.failure is FailureKind.INFORMATION_INSUFFICIENT


def test_proof_absent_does_not_claim_independence():
    diagnosis = MetaGTNTEngine.diagnose_failure({"proof_absent": True})
    assert diagnosis.failure is FailureKind.PROOF_ABSENT
    assert diagnosis.confidence < 1.0
    assert "independence" in diagnosis.rationale[0]


def test_unknown_termination_does_not_claim_undecidability():
    diagnosis = MetaGTNTEngine.diagnose_failure({"termination_unknown": True})
    assert diagnosis.frontier is FrontierKind.COMPUTATIONAL
    assert any("not an undecidability proof" in item for item in diagnosis.rationale)


def test_commutator_advantage_is_order_sensitive_cost_difference():
    assert MetaGTNTEngine.commutator_advantage(cost_ab=3.0, cost_ba=8.0) == 5.0
    assert MetaGTNTEngine.commutator_advantage(cost_ab=8.0, cost_ba=3.0) == -5.0


def test_negative_memory_prunes_exact_dead_path():
    blocked = StrategyPath(("R", "T", "G"), 4.0, CostVector(compute=1), "roots", "raw")
    kept = StrategyPath(("R", "G", "T"), 3.0, CostVector(compute=1), "roots", "lifted")
    memory = NegativeMemory([
        NoGoRule("roots", "raw", "baseline dominates", blocked.signature)
    ])
    engine = MetaGTNTEngine(memory)
    result = engine.select_path([blocked, kept])
    assert result["selected"] == kept
    assert blocked.signature in result["rejected"]


def test_path_score_uses_verified_gain_per_total_cost():
    path = StrategyPath(("R", "OAK"), 9.0, CostVector(compute=2, proof=1, risk=0))
    assert MetaGTNTEngine.path_score(path) == 3.0


def test_firewall_rejects_cycles():
    allowed, reasons = MetaGTNTEngine.firewall_check(("S0", "S1", "S0"), max_depth=5)
    assert not allowed
    assert "circular_dependency_detected" in reasons


def test_firewall_accepts_strict_descent_certificate():
    allowed, reasons = MetaGTNTEngine.firewall_check(
        ("S0", "S1", "S2"), max_depth=4, descent_measure=(3.0, 2.0, 1.0)
    )
    assert allowed
    assert reasons == ()


def test_numeric_result_cannot_jump_to_kernel_verified_without_kernel():
    record = ClaimRecord(
        claim="candidate identity",
        level=TruthLevel.NUMERICALLY_VALIDATED,
        evidence=("1000 numerical samples",),
        countertests=("adversarial sample suite",),
        kernel_verified=False,
    )
    decision = MetaGTNTEngine.promotion_gate(record, TruthLevel.KERNEL_VERIFIED)
    assert not decision["allowed"]
    assert "missing_kernel_verification" in decision["reasons"]


def test_established_status_is_never_auto_promoted():
    record = ClaimRecord(
        claim="candidate theorem",
        level=TruthLevel.INDEPENDENTLY_REPLICATED,
        evidence=("derivation",),
        countertests=("independent negative search",),
        kernel_verified=True,
        independent_replications=2,
    )
    decision = MetaGTNTEngine.promotion_gate(record, TruthLevel.ESTABLISHED_IN_DOMAIN)
    assert not decision["allowed"]
    assert "domain_establishment_requires_external_scientific_consensus" in decision["reasons"]
