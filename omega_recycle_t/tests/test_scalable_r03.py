from omega_recycle.bench import demo_problem
from omega_recycle.flows import ConstrainedRecoveryOptimizer, FlowConstraints
from omega_recycle.scalable import BranchAndBoundRecoveryOptimizer, SearchBudget
from omega_recycle.scoring import ScoringPolicy


def test_branch_and_bound_matches_exact_oracle() -> None:
    materials, candidates = demo_problem()
    policy = ScoringPolicy(energy_shadow_price_per_kwh=0.18, risk_penalty=25.0, preservation_bonus=1.0, future_cycle_weight=0.7)
    constraints = FlowConstraints(max_process_cost=1_000.0, max_energy_kwh=100.0, max_risk_sum=2.0)
    exact = ConstrainedRecoveryOptimizer(materials, policy).optimize(candidates, constraints)
    result = BranchAndBoundRecoveryOptimizer(materials, policy).optimize(
        candidates, constraints, budget=SearchBudget(max_nodes=10_000)
    )
    assert result.optimality_certified is True
    assert result.plan.modes() == exact.plan.modes()
    assert abs(result.plan.total_score - exact.plan.total_score) <= 1e-9
    assert result.evaluated_nodes <= exact.evaluated_combinations + len(candidates) + 1


def test_finite_search_budget_returns_uncertified_incumbent() -> None:
    materials, candidates = demo_problem()
    constraints = FlowConstraints(max_process_cost=1_000.0, max_energy_kwh=100.0, max_risk_sum=2.0)
    result = BranchAndBoundRecoveryOptimizer(materials).optimize(
        candidates, constraints, budget=SearchBudget(max_nodes=3)
    )
    assert result.search_complete is False
    assert result.optimality_certified is False
    assert result.feasible_leaves >= 1
    assert result.optimality_gap_upper_bound >= 0
