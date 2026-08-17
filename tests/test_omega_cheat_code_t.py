from __future__ import annotations

import pytest

from omega_cheat_code_t import (
    EvolutionCandidate,
    EvolutionState,
    MetaDepthTrial,
    ProofEnvelope,
    compile_evolution_plan,
    rank_candidates,
    select_meta_depth,
)


def candidate(name: str, **overrides) -> EvolutionCandidate:
    data = {
        "name": name,
        "success_probability": 0.8,
        "value": 2.0,
        "reuse": 1.5,
        "evidence_gain": 1.2,
        "option_value": 1.1,
        "compute_cost": 1.0,
        "time_cost": 1.0,
        "risk": 0.5,
        "debt": 0.5,
        "verified_marginal_gain": 1.0,
    }
    data.update(overrides)
    return EvolutionCandidate(**data)


def test_expected_evolution_value_penalizes_risk_and_debt() -> None:
    low_penalty = candidate("low", risk=0.1, debt=0.1)
    high_penalty = candidate("high", risk=5.0, debt=5.0)
    assert low_penalty.expected_evolution_value() > high_penalty.expected_evolution_value()


def test_internal_closure_blocks_zero_novelty_duplicate() -> None:
    duplicate = candidate("duplicate", internal_closure_coverage=0.99, novelty_delta=0.0, value=99.0)
    useful = candidate("useful", internal_closure_coverage=0.5, novelty_delta=0.1)
    assert rank_candidates([duplicate, useful]) == [useful]


def test_meta_depth_optimizes_gain_density_not_depth() -> None:
    trials = [
        MetaDepthTrial(1, 4.0, 1.0, 0.1, 0.1),
        MetaDepthTrial(2, 8.0, 8.0, 1.0, 1.0),
        MetaDepthTrial(3, 9.0, 20.0, 3.0, 2.0),
    ]
    assert select_meta_depth(trials).depth == 1


def test_frontier_is_residual_and_surprise_driven() -> None:
    quiet = EvolutionState(10.0, 8.0, surprise=0.0)
    surprising = EvolutionState(10.0, 8.0, surprise=3.0)
    assert surprising.frontier_score() > quiet.frontier_score()
    assert quiet.residual == 2.0


def test_lifecycle_apoptosis_and_distillation() -> None:
    assert candidate("dead", verified_marginal_gain=0.0).lifecycle_action() == "kill"
    assert candidate("compress", capability_retention=0.98, complexity_reduction=0.5).lifecycle_action() == "distill"
    assert candidate("keep", capability_retention=0.8, complexity_reduction=0.5).lifecycle_action() == "keep"


def test_proof_envelope_requires_evidence_and_rollback() -> None:
    valid = ProofEnvelope("faster", ("benchmark.json",), uncertainty=0.1, rollback="abc123")
    invalid = ProofEnvelope("faster", (), uncertainty=1.2, rollback="")
    assert valid.validate() == (True, ())
    ok, errors = invalid.validate()
    assert ok is False
    assert {"evidence_required", "uncertainty_out_of_range", "rollback_required"}.issubset(errors)


def test_plan_is_deterministic_and_oak_safe() -> None:
    state = EvolutionState(10.0, 6.0, surprise=1.0, uncertainty=1.0, opportunity=2.0, evidence=1.0)
    candidates = [candidate("A"), candidate("B", value=1.0)]
    trials = [MetaDepthTrial(1, 2.0, 1.0, 0.1, 0.1)]
    first = compile_evolution_plan("Improve routing", state, candidates, trials)
    second = compile_evolution_plan("Improve routing", state, candidates, trials)
    assert first == second
    assert first.plan_id.startswith("cheat-")
    assert first.proof_required is True
    assert first.automatic_merge is False
    assert first.remote_mutations == 0
    assert first.theorem_claimed is False


def test_plan_rejects_only_redundant_candidates() -> None:
    redundant = candidate("duplicate", internal_closure_coverage=1.0, novelty_delta=0.0)
    with pytest.raises(ValueError, match="no eligible"):
        compile_evolution_plan("x", EvolutionState(1.0, 0.0), [redundant])
