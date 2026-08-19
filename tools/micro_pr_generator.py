"""Micro PR Generator for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Plans focused follow-up PRs. Planning only; does not open PRs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MicroPRPlan:
    plan_id: str
    title: str
    objective: str
    safe_first_step: str


def default_micro_pr_plan() -> tuple[MicroPRPlan, ...]:
    return (
        MicroPRPlan("PR220-MICRO-001", "package safety core", "focus safety routing layer", "create package boundary note"),
        MicroPRPlan("PR220-MICRO-002", "package reality forge", "focus reality/proof artifacts", "create package boundary note"),
        MicroPRPlan("PR220-MICRO-003", "package canon ops", "focus canon graph and rank tools", "create package boundary note"),
        MicroPRPlan("PR220-MICRO-004", "package continuation", "focus continuation and propulsion tools", "create package boundary note"),
        MicroPRPlan("PR220-MICRO-005", "add import smoke tests", "verify new tools load", "create smoke test file"),
        MicroPRPlan("PR220-MICRO-006", "normalize aliases", "map connector-safe aliases", "update alias registry"),
        MicroPRPlan("PR220-MICRO-007", "verify CI path", "focus test execution path", "create CI note"),
        MicroPRPlan("PR220-MICRO-008", "improve navigation", "make stack readable", "update architecture index"),
    )
