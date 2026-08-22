import pytest

from sage_tristan.tensor_discovery_bench import (
    BenchmarkFamily,
    ExposureStatus,
    SystemKind,
    ablate_program,
    build_benchmark_report,
    compile_report,
    default_contamination,
    deterministic_tasks,
    evaluate,
    pareto_front,
    system_profile,
)
from sage_tristan.tensor_research_compiler import ceres_cognitive_program, synthetic_tensor_fixture


def test_all_eight_benchmark_families_are_present():
    tasks = deterministic_tasks()
    assert len(tasks) == 8
    assert {task.family for task in tasks} == set(BenchmarkFamily)
    assert all(task.novelty_scope == "benchmark_only" for task in tasks)
    assert all(task.human_novelty_claimed is False for task in tasks)


def test_historical_contamination_blocks_independent_discovery_eligibility():
    contamination = default_contamination(BenchmarkFamily.HISTORICAL)
    assert contamination.pretraining is ExposureStatus.POSSIBLE
    assert contamination.independent_discovery_eligible is False
    assert "pretraining" in contamination.uncertain_axes
    assert "human" in contamination.uncertain_axes


def test_controlled_synthetic_contamination_can_be_eligible_in_fixture_only():
    contamination = default_contamination(BenchmarkFamily.SYNTHETIC)
    assert contamination.independent_discovery_eligible is True
    assert contamination.uncertain_axes == ()


def test_visible_target_blocks_run_level_independent_discovery_eligibility():
    registry, _ = synthetic_tensor_fixture()
    task = next(task for task in deterministic_tasks() if task.family is BenchmarkFamily.DYNAMIC)
    assert task.contamination.independent_discovery_eligible is True
    assert task.hidden_target is False
    run = evaluate(task, system_profile(SystemKind.SINGLE_LLMT, task, registry))
    assert run.independent_discovery_eligible is False


def test_same_tasks_compare_all_four_system_kinds():
    report = build_benchmark_report()
    by_task = {}
    for run in report.runs:
        by_task.setdefault(run.task_id, set()).add(run.system_kind)
    assert len(by_task) == 8
    assert all(kinds == set(SystemKind) for kinds in by_task.values())


def test_runs_keep_quality_cost_and_contamination_separate():
    registry, _ = synthetic_tensor_fixture()
    task = deterministic_tasks()[0]
    profile = system_profile(SystemKind.META_LLMT, task, registry)
    run = evaluate(task, profile)
    assert 0.0 <= run.capability_coverage <= 1.0
    assert 0.0 <= run.evidence_strength <= 1.0
    assert run.declared_cost > 0
    assert run.discovery_yield == pytest.approx(run.verified_information_gain_proxy / run.declared_cost, abs=1e-6)
    assert run.contamination == task.contamination
    assert run.independent_discovery_claimed is False
    assert run.human_novelty_claimed is False
    assert run.benchmark_proxy_only is True


def test_meta_router_is_adaptive_but_not_declared_superior():
    registry, _ = synthetic_tensor_fixture()
    task = next(task for task in deterministic_tasks() if task.required_capabilities == ("representation_switch",))
    meta = system_profile(SystemKind.META_LLMT, task, registry)
    single = system_profile(SystemKind.SINGLE_LLMT, task, registry)
    assert meta.adaptive_routing is True
    assert single.adaptive_routing is False
    assert single.declared_cost < meta.declared_cost


def test_fixed_coalition_and_meta_can_have_different_costs_even_with_same_coverage():
    registry, _ = synthetic_tensor_fixture()
    task = next(task for task in deterministic_tasks() if task.family is BenchmarkFamily.ADVERSARIAL)
    fixed = evaluate(task, system_profile(SystemKind.FIXED_COALITION, task, registry))
    meta = evaluate(task, system_profile(SystemKind.META_LLMT, task, registry))
    assert fixed.capability_coverage == pytest.approx(1.0)
    assert meta.capability_coverage == pytest.approx(1.0)
    assert fixed.declared_cost != meta.declared_cost


def test_pareto_front_does_not_collapse_to_scalar_intelligence_score():
    report = build_benchmark_report()
    task_id = deterministic_tasks()[0].task_id
    receipt = pareto_front(task_id, report.runs)
    assert receipt.task_id == task_id
    assert receipt.frontier_system_ids
    assert receipt.scalar_intelligence_score_produced is False


def test_program_ablation_is_measured_but_not_promoted_to_causal_proof():
    receipts = ablate_program(ceres_cognitive_program())
    assert len(receipts) == 3
    assert {item.removed_operator_id for item in receipts} == {
        "representation_switch",
        "approximation_residual",
        "invariant_search",
    }
    assert all(item.delta_coverage > 0 for item in receipts)
    assert all(item.causal_effect_proven is False for item in receipts)


def test_suite_summaries_keep_systems_separate():
    report = build_benchmark_report()
    assert len(report.summaries) == 4
    assert {item.system_kind for item in report.summaries} == set(SystemKind)
    assert all(item.total_cost > 0 for item in report.summaries)
    assert all(item.cost_normalized_yield >= 0 for item in report.summaries)


def test_compile_report_exposes_strict_oak_boundaries():
    report = compile_report()
    assert report["release"] == "R0.7"
    assert len(report["task_families"]) == 8
    assert set(report["system_kinds"]) == {item.value for item in SystemKind}
    assert len(report["runs"]) == 32
    assert report["same_task_comparison"] is True
    assert report["all_baselines_retained"] is True
    assert report["cost_normalization_present"] is True
    assert report["contamination_tensor_separate_from_quality"] is True
    assert report["hidden_target_required_for_independent_discovery_eligibility"] is True
    assert report["scalar_intelligence_score_produced"] is False
    assert report["human_novelty_claimed"] is False
    assert report["independent_discovery_certified"] is False
    assert report["meta_llmt_automatically_superior"] is False
    assert report["ablation_is_causal_proof"] is False
    assert report["benchmark_proxy_only"] is True
    assert report["historical_independent_discovery_eligible"] is False


def test_report_historical_contamination_is_explicit_not_erased():
    report = compile_report()
    contamination = report["historical_contamination"]
    assert contamination["pretraining"] is ExposureStatus.POSSIBLE
    assert contamination["human"] is ExposureStatus.UNKNOWN
