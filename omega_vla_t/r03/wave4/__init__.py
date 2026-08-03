"""Ω-VLA-T∞³ R0.3 Wave 4 Counterexample Superfactory."""
from .engine import (
    BUILTINS,
    CounterexampleFrontier,
    CounterexampleRegistry,
    FAMILIES,
    FrontierAddress,
    execute_builtin_campaign,
    generate_environment,
    generate_matrix,
    minimize_counterexample,
    plan_campaign,
    propose_repairs,
    run_oakbench,
    search_counterexample,
    search_matrix_identity,
)
from .models import CounterexampleRecord, SearchPlan, SearchReport, SearchState

__all__ = [
    "BUILTINS",
    "CounterexampleFrontier",
    "CounterexampleRecord",
    "CounterexampleRegistry",
    "FAMILIES",
    "FrontierAddress",
    "SearchPlan",
    "SearchReport",
    "SearchState",
    "execute_builtin_campaign",
    "generate_environment",
    "generate_matrix",
    "minimize_counterexample",
    "plan_campaign",
    "propose_repairs",
    "run_oakbench",
    "search_counterexample",
    "search_matrix_identity",
]
