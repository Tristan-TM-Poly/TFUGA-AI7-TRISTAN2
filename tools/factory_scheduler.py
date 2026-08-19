"""Factory Scheduler for Ω-AIT-RESEARCH-FACTORY-T.

Chooses the safest next production line for a canon branch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FactoryLine(StrEnum):
    REALITY_ANCHOR = "reality_anchor"
    EXPERIMENT = "experiment"
    PROTOTYPE_TESTS = "prototype_tests"
    BENCHMARK = "benchmark"
    REVIEWED_RELEASE = "reviewed_release"
    RISK_REDUCTION = "risk_reduction"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class FactoryScheduleDecision:
    line: FactoryLine
    reason: str
    safe_next_action: str


def schedule_factory_line(
    *,
    reality_level: int,
    proof_level: int,
    canon_rank: int,
    benchmark_level: int = 0,
    risk_high: bool = False,
    debt_high: bool = False,
) -> FactoryScheduleDecision:
    if risk_high:
        return FactoryScheduleDecision(FactoryLine.QUARANTINE, "High risk branch.", "Quarantine or review before action.")
    if debt_high:
        return FactoryScheduleDecision(FactoryLine.RISK_REDUCTION, "Debt is high.", "Reduce risk/proof debt before stronger claims.")
    if reality_level < 3:
        return FactoryScheduleDecision(FactoryLine.REALITY_ANCHOR, "Idea is not yet a testable hypothesis.", "Add RealityAnchor and claim status.")
    if proof_level < 3:
        return FactoryScheduleDecision(FactoryLine.EXPERIMENT, "Hypothesis needs experiment.", "Build minimal experiment plan.")
    if canon_rank < 6:
        return FactoryScheduleDecision(FactoryLine.PROTOTYPE_TESTS, "Branch needs tested prototype.", "Create or test a reversible prototype.")
    if benchmark_level < 3:
        return FactoryScheduleDecision(FactoryLine.BENCHMARK, "Tool lacks useful baseline.", "Add simple baseline benchmark.")
    return FactoryScheduleDecision(FactoryLine.REVIEWED_RELEASE, "Branch is mature enough for reviewed release planning.", "Prepare reviewed note/demo/release plan; no auto-publish.")
