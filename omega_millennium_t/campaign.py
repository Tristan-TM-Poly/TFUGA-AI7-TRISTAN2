"""Cross-problem research campaign compiler."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Iterable

from .models import ProblemId, StrategyScore
from .registry import all_problems
from .strategy import allocate_finite_budget


def default_strategies() -> tuple[StrategyScore, ...]:
    return (
        StrategyScore("poincare-proof-reconstruction", ProblemId.POINCARE, .75, .95, .80, .25, .60, .35, .25, .20, evidence_for=3),
        StrategyScore("rh-positivity-kernel", ProblemId.RIEMANN, .80, .55, .65, .75, .95, .75, .80, .80),
        StrategyScore("rh-spectral-operator-audit", ProblemId.RIEMANN, .70, .45, .55, .85, .95, .85, .90, .90),
        StrategyScore("pnp-barrier-aware-lower-bounds", ProblemId.P_VS_NP, .85, .55, .75, .70, 1.0, .80, .85, .85),
        StrategyScore("ns-critical-scale-blowup-microscope", ProblemId.NAVIER_STOKES, .90, .75, .70, .70, 1.0, .65, .70, .65, evidence_for=1),
        StrategyScore("ns-monotone-functional-forge", ProblemId.NAVIER_STOKES, .85, .70, .75, .75, 1.0, .70, .75, .70),
        StrategyScore("ym-uniform-gap-tracker", ProblemId.YANG_MILLS, .90, .55, .65, .75, 1.0, .90, .90, .85),
        StrategyScore("hodge-cycle-cohomology-bridge", ProblemId.HODGE, .75, .45, .70, .65, .90, .80, .85, .80),
        StrategyScore("bsd-rank-discrepancy-certifier", ProblemId.BSD, .80, .80, .75, .55, .90, .55, .60, .55),
    )


def compile_campaign(
    *,
    total_budget_units: int = 100,
    strategies: Iterable[StrategyScore] | None = None,
) -> dict[str, object]:
    strategies = tuple(strategies) if strategies is not None else default_strategies()
    allocations = allocate_finite_budget(strategies, total_budget_units=total_budget_units)
    problem_counts = {problem.problem_id.value: 0 for problem in all_problems()}
    for allocation in allocations:
        problem_counts[allocation.problem_id.value] += allocation.finite_budget_units
    payload: dict[str, object] = {
        "schema": "omega-millennium-campaign/1",
        "total_budget_units": total_budget_units,
        "allocations": [asdict(item) for item in allocations],
        "problem_budget_units": problem_counts,
        "all_fronts_may_remain_open": True,
        "current_batch_is_finite": True,
        "permanent_total_cap": None,
        "solution_claimed": False,
        "scientific_validation_claimed": False,
    }
    payload["digest"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
    return payload
