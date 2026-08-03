from __future__ import annotations

from dataclasses import replace

from .analyzer import ResolutionAnalyzer
from .engine import ResolutionEngine
from .families import FAMILIES
from .models import ResolutionPolicy


def run_r04_benchmark(problem_budget: int = 4096) -> dict[str, object]:
    full_policy = ResolutionPolicy(
        problem_budget=problem_budget,
        max_attempts_per_problem=2,
        permanent_total_cap=None,
    )
    first = ResolutionEngine().run(full_policy)
    second = ResolutionEngine().run(full_policy)
    restricted = ResolutionEngine().run(
        replace(full_policy, max_attempts_per_problem=1)
    )
    analysis = ResolutionAnalyzer().analyze(first)

    first_payload = first.to_dict(include_records=False)
    second_payload = second.to_dict(include_records=False)
    deterministic = first.to_dict() == second.to_dict()
    family_ids = {metric.family_id for metric in first.family_metrics}
    fallback_solutions = sum(metric.fallback_solves for metric in first.family_metrics)
    counterexamples = sum(metric.counterexamples for metric in first.family_metrics)
    invariants = {
        "all_families_covered": family_ids == {family.family_id for family in FAMILIES},
        "materialized_budget_exact": first.materialized_problems == problem_budget,
        "all_full_portfolio_fixtures_solved": first.unresolved_problems == 0,
        "full_portfolio_solve_rate_one": first.solve_rate == 1.0,
        "fallback_path_exercised": fallback_solutions > 0,
        "counterexamples_preserved": counterexamples > 0,
        "restricted_portfolio_exposes_unresolved": restricted.unresolved_problems > 0,
        "deterministic_full_receipt": deterministic,
        "receipt_hash_valid": first.verify_hash(),
        "no_permanent_total_cap": first.permanent_total_cap is None,
        "no_open_problem_claim": first.claims["open_problem_solution_claimed"] is False,
        "no_general_correctness_claim": first.claims["general_algorithm_correctness_claimed"] is False,
        "analysis_does_not_claim_maximum": analysis["claims"]["maximum_problem_resolution_claimed"] is False,
    }
    certified = all(invariants.values())
    return {
        "status": (
            "CERTIFIED_SYNTHETIC_PROBLEM_RESOLUTION_FIXTURES_R0_4"
            if certified
            else "OAK_INVARIANT_FAILURE_R0_4"
        ),
        "system": "omega-code-dojo-t-infinity",
        "version": "R0.4",
        "logical_problem_space": first.logical_problem_space,
        "family_count": len(FAMILIES),
        "materialized_problems": first.materialized_problems,
        "solved_problems": first.solved_problems,
        "unresolved_problems": first.unresolved_problems,
        "solve_rate": first.solve_rate,
        "total_attempts": first.total_attempts,
        "total_cost_units": first.total_cost_units,
        "fallback_solutions": fallback_solutions,
        "counterexamples": counterexamples,
        "restricted_unresolved": restricted.unresolved_problems,
        "permanent_total_cap": first.permanent_total_cap,
        "deterministic": deterministic,
        "receipt_sha256": first.receipt_sha256,
        "invariants": invariants,
        "claims": dict(first.claims),
        "family_metrics": [metric.to_dict() for metric in first.family_metrics],
        "best_learning_analysis": analysis,
        "receipt_summary": first_payload,
        "second_receipt_summary": second_payload,
    }
