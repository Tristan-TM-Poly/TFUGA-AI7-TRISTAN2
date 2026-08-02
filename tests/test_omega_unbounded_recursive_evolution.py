from __future__ import annotations

import hashlib
import json

import pytest

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
