"""Autonomous Sprint Cell for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Creates a small safe sprint that ends with an artifact, a check, a reduced gap,
and a next move. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SprintCell:
    sprint_goal: str
    scope: str
    safe_actions: tuple[str, ...]
    artifacts: tuple[str, ...]
    checks: tuple[str, ...]
    reduced_items: tuple[str, ...]
    oak_status: str
    next_sprint: str


def create_sprint_cell(goal: str, *, scope: str = "draft_pr") -> SprintCell:
    return SprintCell(
        sprint_goal=goal,
        scope=scope,
        safe_actions=("create_artifact", "add_check", "record_trace"),
        artifacts=("doc_or_tool_or_test",),
        checks=("minimal_regression_or_consistency_check",),
        reduced_items=("one_visible_gap",),
        oak_status="draft_only_no_external_effect",
        next_sprint="choose_next_safe_queue_item",
    )
