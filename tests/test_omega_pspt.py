from sage_tristan.omega_pspt import (
    CLAIM_LEVEL_TO_MIN_OAK,
    OAKLevel,
    OMEGA_TFTS,
    BayesTristanPosterior,
    PhaseCard,
    artifact_penalty,
    cycle_rank,
    hyperloop_score,
    should_promote_phase,
)


def test_claim_level_mapping_is_ordered():
    assert CLAIM_LEVEL_TO_MIN_OAK["vision"] == OAKLevel.OAK_0
    assert CLAIM_LEVEL_TO_MIN_OAK["candidate"] == OAKLevel.OAK_1
    assert CLAIM_LEVEL_TO_MIN_OAK["replicated_phase"] == OAKLevel.OAK_6


def test_cycle_rank_counts_independent_cycles():
    assert cycle_rank(num_vertices=4, num_edges=4, components=1) == 1
    assert cycle_rank(num_vertices=3, num_edges=2, components=1) == 0


def test_hyperloop_score_is_positive_for_loops():
    assert hyperloop_score([0, 1, 3]) > 0


def test_posterior_validates_range():
    posterior = BayesTristanPosterior(
        truth_probability=0.2,
        utility=0.8,
        fertility=0.9,
        testability=0.7,
        safety=0.9,
        profitability=0.4,
        compressibility=0.8,
        replicability=0.5,
    )
    assert 0 <= posterior.action_score() <= 1


def test_claim_allowed_only_when_oak_supports_it():
    card = PhaseCard(
        phase_id="test",
        name="test",
        oak_level=OAKLevel.OAK_1,
        claim_level="candidate",
    )
    assert card.is_claim_allowed()

    overclaim = PhaseCard(
        phase_id="test2",
        name="test2",
        oak_level=OAKLevel.OAK_1,
        claim_level="replicated_phase",
    )
    assert not overclaim.is_claim_allowed()


def test_artifact_penalty_detects_overlap():
    penalty = artifact_penalty(
        ["contact_short", "thermal_drift"],
        ["contact_short", "contamination"],
    )
    assert penalty > 0


def test_should_promote_phase_blocks_falsifier():
    assert not should_promote_phase(
        OMEGA_TFTS,
        OAKLevel.OAK_1,
        observed_falsifiers=["contact_short"],
    )


def test_omega_tfts_is_candidate_not_replicated_phase():
    assert OMEGA_TFTS.is_claim_allowed()
    assert OMEGA_TFTS.oak_level == OAKLevel.OAK_1
    assert OMEGA_TFTS.claim_level == "candidate"
    assert OMEGA_TFTS.missing_for_promotion(OAKLevel.OAK_6)
