import pytest

from omega_compute_physics_t.bottleneck_dynamics import BottleneckObservation, trace_bottleneck_migration
from omega_compute_physics_t.opportunity_engine import OpportunityEvidence, rank_optimization_opportunities, score_optimization_opportunity
from omega_compute_physics_t.optimization_arena import VariantEvidence, run_optimization_arena
from omega_compute_physics_t.optimization_credit import shapley_optimization_credit
from omega_compute_physics_t.optimization_genome import OptimizationGene, WorkloadSignature, rank_transfer_candidates
from omega_compute_physics_t.optimization_portfolio import PortfolioOpportunity, optimize_portfolio
from omega_compute_physics_t.transformation_algebra import canonical_transformation_library, compose_transformations


def test_opportunity_engine_separates_remeasure_from_optimize():
    stale = OpportunityEvidence(
        repository="r", node="stale", static_complexity=3, graph_centrality=2,
        usage_weight=10, regression_signal=1, expected_savings_prior=0.5,
        confidence_debt=0.8, engineering_effort_hours=2, benchmark_cost=1,
    )
    fresh = OpportunityEvidence(
        repository="r", node="fresh", static_complexity=3, graph_centrality=2,
        usage_weight=10, regression_signal=1, expected_savings_prior=0.5,
        confidence_debt=0.1, engineering_effort_hours=2, benchmark_cost=1,
    )
    assert score_optimization_opportunity(stale).action == "remeasure-first"
    assert score_optimization_opportunity(fresh).action == "optimize-regression"
    ranked = rank_optimization_opportunities((stale, fresh))
    assert ranked[0].node == "fresh"


def test_transformation_algebra_composes_and_rejects_duplicates():
    library = canonical_transformation_library()
    program = compose_transformations((library[0], library[6]))
    assert program.ids() == ("preallocate", "vectorize")
    assert "numerical-order-change" in program.risk_union
    with pytest.raises(ValueError):
        compose_transformations((library[0], library[0]))


def test_optimization_arena_uses_correctness_and_pareto():
    baseline = VariantEvidence("base", {"time": 10.0, "memory": 10.0})
    fast = VariantEvidence("fast", {"time": 5.0, "memory": 12.0}, confidence=0.9)
    lean = VariantEvidence("lean", {"time": 9.0, "memory": 6.0}, confidence=0.9)
    broken = VariantEvidence("broken", {"time": 1.0, "memory": 1.0}, correctness_passed=False)
    report = run_optimization_arena(
        baseline, (fast, lean, broken), directions={"time": "minimize", "memory": "minimize"}
    )
    assert "fast" in report.pareto_front
    assert "lean" in report.pareto_front
    broken_score = next(row for row in report.scores if row.variant_id == "broken")
    assert not broken_score.eligible
    assert report.best_variant in {"fast", "lean"}


def test_optimization_gene_transfer_is_priority_not_proof():
    gene = OptimizationGene(
        gene_id="g1", source_repository="A", source_node="f",
        transformation_ids=("preallocate",),
        context={"loops": 2.0, "allocations": 4.0},
        measured_gain=0.3, domain="n=1k..10k", hardware_id="h1", evidence_level="L4",
    )
    workloads = (
        WorkloadSignature("B", "g", {"loops": 2.0, "allocations": 4.0}),
        WorkloadSignature("C", "h", {"loops": 0.0, "allocations": 1.0}),
    )
    rows = rank_transfer_candidates((gene,), workloads, minimum_similarity=0.9)
    assert rows[0].destination_node == "g"
    assert rows[0].similarity == pytest.approx(1.0)


def test_exact_shapley_credit_matches_two_transform_ablation():
    values = {
        frozenset(): 0.0,
        frozenset({"a"}): 1.0,
        frozenset({"b"}): 2.0,
        frozenset({"a", "b"}): 4.0,
    }
    rows = {row.transformation_id: row.shapley_credit for row in shapley_optimization_credit(("a", "b"), values)}
    assert rows["a"] == pytest.approx(1.5)
    assert rows["b"] == pytest.approx(2.5)
    assert sum(rows.values()) == pytest.approx(4.0)


def test_bottleneck_migration_records_resource_shift():
    report = trace_bottleneck_migration((
        BottleneckObservation("c1", {"cpu": 0.7, "memory": 0.3}),
        BottleneckObservation("c2", {"cpu": 0.4, "memory": 0.6}),
        BottleneckObservation("c3", {"cpu": 0.2, "memory": 0.8}),
    ))
    assert report.migration_count == 1
    assert report.transitions[0].from_resource == "cpu"
    assert report.transitions[0].to_resource == "memory"


def test_portfolio_respects_budget_probability_and_synergy():
    rows = (
        PortfolioOpportunity("a", expected_value=8, effort_cost=4, success_probability=1.0),
        PortfolioOpportunity("b", expected_value=6, effort_cost=3, success_probability=0.5),
        PortfolioOpportunity("c", expected_value=5, effort_cost=2, success_probability=1.0),
    )
    plan = optimize_portfolio(rows, effort_budget=6, interactions={("a", "c"): 2.0})
    assert plan.selected == ("a", "c")
    assert plan.total_effort == pytest.approx(6.0)
    assert plan.expected_value == pytest.approx(15.0)
    assert plan.interaction_value == pytest.approx(2.0)


def test_portfolio_has_explicit_combinatorial_guard():
    rows = tuple(PortfolioOpportunity(str(i), 1, 1) for i in range(19))
    with pytest.raises(ValueError):
        optimize_portfolio(rows, effort_budget=10)
