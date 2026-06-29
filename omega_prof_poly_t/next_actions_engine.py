"""Top next actions engine for Omega absorb v1.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .department_bridge_optimizer import OptimizedBridge
from .poly_research_twin_v2 import PolyResearchTwinV2


@dataclass(frozen=True)
class NextAction:
    rank: int
    action: str
    source: str
    score: float
    packet_type: str


@dataclass(frozen=True)
class NextActionPlan:
    actions: Tuple[NextAction, ...]
    next_action: str


def compile_top_next_actions(twin: PolyResearchTwinV2, bridges: Iterable[OptimizedBridge] = (), limit: int = 10) -> NextActionPlan:
    actions = []
    for item in twin.best_course_modules[:3]:
        actions.append(NextAction(0, item, "course", 0.72, "course_packet"))
    for item in twin.best_lab_projects[:3]:
        actions.append(NextAction(0, item, "project", 0.70, "project_packet"))
    for item in twin.best_ip_candidates[:2]:
        actions.append(NextAction(0, item, "ip", 0.68, "ip_packet"))
    for bridge in tuple(bridges)[:3]:
        actions.append(NextAction(0, f"{bridge.professor_a} x {bridge.professor_b}", "bridge", bridge.score, "bridge_packet"))
    for item in twin.missing_evidence[:2]:
        actions.append(NextAction(0, item, "evidence", 0.55, "evidence_packet"))
    ranked = sorted(actions, key=lambda action: action.score, reverse=True)[:limit]
    return NextActionPlan(
        actions=tuple(
            NextAction(index, action.action, action.source, action.score, action.packet_type)
            for index, action in enumerate(ranked, start=1)
        ),
        next_action="render_or_execute_local_action_packets",
    )


def render_next_actions_markdown(plan: NextActionPlan) -> str:
    lines = ["# Omega Absorb Top Next Actions", ""]
    for action in plan.actions:
        lines.append(f"{action.rank}. {action.action} [{action.packet_type}] score={action.score:.4f}")
    return "\n".join(lines).strip() + "\n"
