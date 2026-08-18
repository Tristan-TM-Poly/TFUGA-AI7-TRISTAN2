from __future__ import annotations

import hashlib
import json

import pytest

from omega_unbounded_t.phase_evolution import (
    CapacityEnvelope,
    MutationCandidate,
    PhaseAction,
    PhaseEvolutionEngine,
    PhasePolicy,
    PhaseState,
)
from omega_unbounded_t.recursive_evolution import (
    AdversarialOAKBench,
    AdversarialScenario,
    CandidateProfile,
    CanaryPolicy,
    CanaryPromotionEngine,
    CanarySample,
    ProofBundleWriter,
    RecursiveEvolutionLab,
    default_adversarial_scenarios,
)


def _baseline_profile() -> CandidateProfile:
    return CandidateProfile(
        "incumbent",
        throughput=100.0,
        memory_bytes=1_000_000,
        latency_ms=100.0,
        quality=0.99,
        recovery_rate=0.99,
        complexity=1.0,
        overshoot=0.20,
    )


def _phase_state(**overrides: object) -> PhaseState:
    values: dict[str, object] = {
        "capacities": CapacityEnvelope(
            compute=100.0,
            agents=90.0,
            humans=70.0,
            proof=50.0,
            memory=80.0,
            governance=60.0,
        ),
        "residual_pressure": 0.20,
        "debt_pressure": 0.20,
        "latency_pressure": 0.20,
        "compute_cost_pressure": 0.20,
        "human_friction": 0.20,
        "verified_capability_index": 0.70,
        "regeneration_index": 0.70,
        "independence_index": 0.65,
        "observability_index": 0.80,
        "human_dependency_index": 0.30,
        "persistent_complexity": 1.0,
    }
    values.update(overrides)
    return PhaseState(**values)  # type: ignore[arg-type]


def _phase_evaluate(
    engine: PhaseEvolutionEngine,
    state: PhaseState,
    **overrides: float,
):
    inputs = {
        "generation_rate": 20.0,
        "expected_residual_reduction": 0.20,
        "migration_cost": 0.20,
        "migration_risk": 0.20,
        "induced_debt": 0.20,
        "uncertainty": 0.10,
    }
    inputs.update(overrides)
    return engine.evaluate(state, **inputs)


def test_adversarial_bench_rejects_fragile_recovery() -> None:
    profile = CandidateProfile(
        "fragile",
        throughput=150.0,
        memory_bytes=900_000,
        latency_ms=80.0,
        quality=0.97,
        recovery_rate=0.60,
        complexity=1.2,
        overshoot=0.8,
    )
    result = AdversarialOAKBench(
        quality_floor=0.94,
        recovery_floor=0.50,
    ).evaluate(profile, default_adversarial_scenarios())

    assert result.hard_gates_passed is False
    assert "checkpoint-corruption:recovery_floor" in result.failures


def test_remote_mutation_is_a_hard_gate() -> None:
    profile = CandidateProfile(
        "unsafe",
        throughput=100.0,
        memory_bytes=1_000_000,
        latency_ms=100.0,
        quality=0.99,
        recovery_rate=0.99,
        complexity=1.0,
        overshoot=0.2,
        remote_mutations=1,
    )
    result = AdversarialOAKBench().evaluate(
        profile,
        (AdversarialScenario("nominal"),),
    )
    assert result.hard_gates_passed is False
    assert "nominal:remote_mutation" in result.failures


def test_canary_advances_then_rolls_back() -> None:
    baseline = AdversarialOAKBench(
        quality_floor=0.94,
        recovery_floor=0.50,
    ).evaluate(_baseline_profile(), default_adversarial_scenarios())
    samples = (
        CanarySample(0.01, 0.99, 90.0, 1_050_000, 0.99),
        CanarySample(0.05, 0.99, 90.0, 1_050_000, 0.99),
        CanarySample(0.20, 0.90, 90.0, 1_050_000, 0.99),
        CanarySample(0.50, 0.90, 90.0, 1_050_000, 0.99),
        CanarySample(1.00, 0.90, 90.0, 1_050_000, 0.99),
    )
    report = CanaryPromotionEngine(CanaryPolicy()).run(
        baseline=baseline,
        samples=samples,
        rollback_target=baseline.profile.fingerprint,
    )

    assert report.status == "rolled_back"
    assert [item.action for item in report.decisions] == [
        "ADVANCE",
        "ADVANCE",
        "ROLLBACK",
    ]
    assert report.rollback_plan["trigger_stage"] == 0.20
    assert report.rollback_plan["automatic_execution"] is False


def test_canary_requires_exact_stage_sequence() -> None:
    baseline = AdversarialOAKBench(
        quality_floor=0.94,
        recovery_floor=0.50,
    ).evaluate(_baseline_profile(), default_adversarial_scenarios())
    with pytest.raises(ValueError, match="exactly match"):
        CanaryPromotionEngine().run(
            baseline=baseline,
            samples=(CanarySample(1.0, 0.99, 90.0, 900_000, 0.99),),
            rollback_target=baseline.profile.fingerprint,
        )


def test_proof_bundle_is_content_addressed(tmp_path) -> None:
    scenarios = default_adversarial_scenarios()
    aggregate = AdversarialOAKBench(
        quality_floor=0.94,
        recovery_floor=0.50,
    ).evaluate(_baseline_profile(), scenarios)
    canary = CanaryPromotionEngine().run(
        baseline=aggregate,
        samples=tuple(
            CanarySample(stage, 0.99, 90.0, 900_000, 0.99)
            for stage in CanaryPolicy().stages
        ),
        rollback_target=aggregate.profile.fingerprint,
    )
    manifest = ProofBundleWriter(tmp_path).write(
        aggregate=aggregate,
        scenarios=scenarios,
        canary=canary,
        authority={
            "source_mutations": 0,
            "remote_mutations": 0,
            "automatic_merge": False,
        },
    )

    bundle = tmp_path / aggregate.profile.fingerprint
    stored = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert stored["bundle_id"] == manifest["bundle_id"]
    for name, expected in stored["files"].items():
        actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        assert actual == expected


def test_recursive_evolution_lab_is_oak_gated(tmp_path) -> None:
    report = RecursiveEvolutionLab(tmp_path).run()

    assert report["status"] == "passed"
    assert set(report["pareto_front"]) == {"fast", "lean"}
    assert report["dominated"] == ["dominated"]
    assert report["rejected"] == ["fragile"]
    assert report["safe_canary"]["status"] == "promotion_candidate"
    assert report["rollback_demonstration"]["status"] == "rolled_back"
    assert report["rollback_demonstration"]["decisions"][-1]["stage"] == 0.20
    assert report["authority"]["scalar_score_has_final_authority"] is False
    assert report["authority"]["source_mutations"] == 0
    assert report["authority"]["remote_mutations"] == 0
    assert report["authority"]["automatic_merge"] is False
    assert (tmp_path / "evolution-report.json").exists()
    assert (tmp_path / "m_minus.jsonl").stat().st_size > 0
    assert (tmp_path / "m_plus.jsonl").stat().st_size > 0
    assert report["proof_bundles"]["fast"]["bundle_id"]


def test_phase_capacity_uses_verified_bottleneck() -> None:
    capacities = CapacityEnvelope(100, 90, 70, 50, 80, 60)
    assert capacities.effective == 50
    assert capacities.bottleneck == "proof"


def test_phase_decision_is_state_driven_not_calendar_driven() -> None:
    engine = PhaseEvolutionEngine()
    state = _phase_state()
    first = _phase_evaluate(engine, state)
    second = _phase_evaluate(engine, state)
    assert first.phase == second.phase
    assert first.action == second.action
    assert first.transition_pressure == second.transition_pressure


def test_phase_critical_pressure_with_evidence_proposes_reversible_mutation() -> None:
    engine = PhaseEvolutionEngine()
    state = _phase_state(
        residual_pressure=0.95,
        debt_pressure=0.80,
        latency_pressure=0.75,
        compute_cost_pressure=0.70,
        human_friction=0.70,
    )
    decision = _phase_evaluate(
        engine,
        state,
        expected_residual_reduction=0.80,
        migration_cost=0.20,
        migration_risk=0.15,
        induced_debt=0.10,
        uncertainty=0.45,
    )
    assert decision.action is PhaseAction.MUTATE
    assert decision.distance_to_transition == 0.0
    assert decision.reversible_required is True
    assert decision.automatic_execution is False


def test_phase_critical_pressure_without_evidence_compresses_and_observes() -> None:
    engine = PhaseEvolutionEngine()
    state = _phase_state(
        residual_pressure=0.90,
        debt_pressure=0.80,
        latency_pressure=0.70,
        compute_cost_pressure=0.70,
        human_friction=0.70,
    )
    decision = _phase_evaluate(
        engine,
        state,
        expected_residual_reduction=0.10,
        migration_cost=0.40,
        migration_risk=0.30,
        induced_debt=0.20,
    )
    assert decision.action is PhaseAction.COMPRESS_AND_OBSERVE


def test_phase_generation_over_absorption_throttles_before_mutation() -> None:
    engine = PhaseEvolutionEngine()
    decision = _phase_evaluate(
        engine,
        _phase_state(),
        generation_rate=60.0,
        expected_residual_reduction=1.0,
        migration_cost=0.01,
        migration_risk=0.01,
        induced_debt=0.01,
    )
    assert decision.criticality_ratio == pytest.approx(1.2)
    assert decision.action is PhaseAction.THROTTLE_GENERATION


def test_phase_uncertainty_increases_reversibility_requirement() -> None:
    engine = PhaseEvolutionEngine()
    low = _phase_evaluate(engine, _phase_state(), uncertainty=0.10)
    high = _phase_evaluate(engine, _phase_state(), uncertainty=0.80)
    assert low.reversible_required is False
    assert high.reversible_required is True


def test_phase_regeneration_audit_accepts_capability_preserving_distillation() -> None:
    engine = PhaseEvolutionEngine()
    before = _phase_state()
    after = _phase_state(
        verified_capability_index=0.71,
        regeneration_index=0.72,
        persistent_complexity=0.70,
    )
    audit = engine.audit_regeneration(before, after)
    assert audit.passed is True
    assert audit.capacity_conservation >= 1.0
    assert audit.regeneration_conservation >= 1.0
    assert audit.complexity_ratio == pytest.approx(0.70)


def test_phase_regeneration_audit_blocks_destructive_apoptosis() -> None:
    engine = PhaseEvolutionEngine(
        PhasePolicy(
            minimum_capacity_conservation=0.98,
            minimum_regeneration_conservation=0.95,
        )
    )
    before = _phase_state()
    after = _phase_state(
        verified_capability_index=0.50,
        regeneration_index=0.60,
        persistent_complexity=0.40,
    )
    audit = engine.audit_regeneration(before, after)
    assert audit.passed is False
    assert any("capability loss" in reason for reason in audit.reasons)


def test_phase_mutation_ranking_penalizes_cost_risk_and_debt() -> None:
    current = _phase_state()
    cheap = MutationCandidate(
        "cheap",
        expected_residual_reduction=0.60,
        verified_capability_after=0.76,
        migration_cost=0.10,
        migration_risk=0.10,
        induced_debt=0.05,
        reversibility=0.90,
    )
    expensive = MutationCandidate(
        "expensive",
        expected_residual_reduction=0.90,
        verified_capability_after=0.80,
        migration_cost=0.80,
        migration_risk=0.60,
        induced_debt=0.40,
        reversibility=0.40,
    )
    ranked = PhaseEvolutionEngine.rank_mutations(current, (expensive, cheap))
    assert [item.name for item in ranked] == ["cheap", "expensive"]


def test_phase_capacity_dimensions_must_be_positive() -> None:
    with pytest.raises(ValueError, match="proof capacity must be positive"):
        CapacityEnvelope(100, 90, 70, 0, 80, 60)
