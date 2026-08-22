from sage_tristan.tensor_research_compiler import synthetic_tensor_fixture
from sage_tristan.tensor_risk_gate import (
    CumulativeRiskTensorCompiler,
    compile_report,
    synthetic_cumulative_risk_fixture,
)


def test_standard_fixture_still_selects_complementary_a_b_within_budget():
    registry, problem = synthetic_tensor_fixture()
    receipt = CumulativeRiskTensorCompiler(registry).compile(problem, max_llmts=3)
    assert receipt.selected_person_ids == ("person_a", "person_b")
    assert receipt.uncovered_capabilities == ()
    assert receipt.cumulative_risk == 0.10
    assert receipt.risk_budget == 0.5
    assert receipt.cumulative_risk_within_budget is True
    assert receipt.risk_aggregation_model == "additive_declared_proxy"
    assert receipt.portfolio_risk_optimality_proven is False
    assert receipt.risk_independence_assumed is False
    assert receipt.full_tensor_materialized is False


def test_two_individually_admissible_people_cannot_exceed_cumulative_budget():
    registry, problem = synthetic_cumulative_risk_fixture()
    assert all(person.risk <= problem.risk_budget for person in registry.llmts)
    receipt = CumulativeRiskTensorCompiler(registry).compile(problem, max_llmts=2)
    assert len(receipt.selected_person_ids) == 1
    assert len(receipt.uncovered_capabilities) == 1
    assert receipt.cumulative_risk == 0.30
    assert receipt.cumulative_risk_within_budget is True
    assert receipt.stop_reason == "cumulative_risk_budget_exhausted"


def test_zero_or_tiny_budget_can_fail_closed_without_selection():
    registry, problem = synthetic_cumulative_risk_fixture()
    constrained = problem.__class__(
        problem.problem_id,
        problem.capability_tags,
        problem.domain_tags,
        problem.initial_representation_ids,
        problem.target_representation_ids,
        problem.evidence_ids,
        risk_budget=0.10,
    )
    receipt = CumulativeRiskTensorCompiler(registry).compile(constrained)
    assert receipt.selected_person_ids == ()
    assert set(receipt.uncovered_capabilities) == set(problem.capability_tags)
    assert receipt.cumulative_risk == 0.0
    assert receipt.stop_reason == "cumulative_risk_budget_exhausted"


def test_report_preserves_oak_boundaries():
    report = compile_report()
    assert report["release"] == "R0.6.1"
    assert report["per_agent_risk_is_coalition_risk"] is False
    assert report["cumulative_risk_gate_present"] is True
    assert report["risk_aggregation_model"] == "additive_declared_proxy"
    assert report["portfolio_risk_optimality_proven"] is False
    assert report["risk_independence_assumed"] is False
    assert report["real_world_safety_certified"] is False
    constrained = report["cumulative_risk_fixture"]
    assert constrained["cumulative_risk"] <= constrained["risk_budget"]
    assert len(constrained["selected_person_ids"]) == 1
    assert len(constrained["uncovered_capabilities"]) == 1
