from sage_tristan.omega_math_tristan import (
    BayesTristanVector,
    ClaimCard,
    action_score,
    canonicalization_score,
    classify_oak_status,
    next_action_hint,
    oak_maturity,
    rank_claims,
)


def test_oak_maturity_normalizes_levels():
    assert oak_maturity("OAK-0") == 0.0
    assert oak_maturity("OAK-5") == 0.5
    assert oak_maturity("OAK-10") == 1.0


def test_action_score_rewards_testable_fertile_low_risk_claims():
    strong = BayesTristanVector(
        probability=0.7,
        utility=0.9,
        fertility=0.9,
        testability=0.9,
        compressibility=0.7,
        risk=0.1,
        oak_maturity=0.4,
    )
    weak = BayesTristanVector(
        probability=0.4,
        utility=0.4,
        fertility=0.4,
        testability=0.2,
        compressibility=0.3,
        risk=0.9,
        oak_maturity=0.1,
    )
    assert action_score(strong) > action_score(weak)


def test_canonicalization_penalizes_illusion_and_cost():
    vector = BayesTristanVector(
        probability=0.8,
        utility=0.8,
        fertility=0.8,
        testability=0.8,
        compressibility=0.8,
        risk=0.2,
        oak_maturity=0.7,
    )
    clean = canonicalization_score(vector, cost=0.0, illusion=0.0)
    expensive_illusory = canonicalization_score(vector, cost=1.0, illusion=1.0)
    assert clean > expensive_illusory


def test_classify_oak_status_uses_conservative_gates():
    assert classify_oak_status(
        has_definition=False,
        has_conjecture=False,
        has_prototype=False,
        has_baseline=False,
        has_robust_validation=False,
        has_partial_proof=False,
        has_full_proof=False,
    ) == "OAK-0"
    assert classify_oak_status(
        has_definition=True,
        has_conjecture=True,
        has_prototype=True,
        has_baseline=True,
        has_robust_validation=True,
        has_partial_proof=False,
        has_full_proof=False,
    ) == "OAK-5"
    assert classify_oak_status(
        has_definition=True,
        has_conjecture=True,
        has_prototype=True,
        has_baseline=True,
        has_robust_validation=True,
        has_partial_proof=True,
        has_full_proof=True,
        reused_across_branches=True,
    ) == "OAK-9"


def test_next_action_hint_promotes_only_mature_claims():
    vector = BayesTristanVector(0.5, 0.5, 0.5, 0.5, 0.5, 0.2, 0.2)
    card = ClaimCard(
        id="C1",
        title="conjecture",
        statement="A testable conjecture.",
        branch="CVCD",
        oak_status="OAK-2",
        claim_type="conjecture",
        bayes_tristan=vector,
    )
    assert next_action_hint(card) == "build_prototype"

    mature = ClaimCard(
        id="T1",
        title="theorem",
        statement="A proved reusable theorem.",
        branch="HGFM",
        oak_status="OAK-7",
        claim_type="theorem",
        bayes_tristan=vector,
    )
    assert next_action_hint(mature) == "promote_to_canon"


def test_rank_claims_sorts_descending():
    low = ClaimCard(
        id="low",
        title="low",
        statement="low",
        branch="Other",
        oak_status="OAK-1",
        claim_type="intuition",
        bayes_tristan=BayesTristanVector(0.1, 0.1, 0.1, 0.1, 0.1, 0.8, 0.1),
    )
    high = ClaimCard(
        id="high",
        title="high",
        statement="high",
        branch="FFWT_HAC_CVCD",
        oak_status="OAK-4",
        claim_type="prototype",
        bayes_tristan=BayesTristanVector(0.7, 0.9, 0.9, 0.9, 0.7, 0.1, 0.4),
    )
    ranked = rank_claims([low, high])
    assert ranked[0][1].id == "high"
