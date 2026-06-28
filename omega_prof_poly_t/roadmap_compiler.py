"""Portfolio to roadmap compiler for Omega absorb v0.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .portfolio_optimizer import PortfolioSelection


@dataclass(frozen=True)
class RoadmapStep:
    order: int
    atom_id: str
    path: str
    score: float
    deliverable: str
    success_check: str


@dataclass(frozen=True)
class RoadmapPlan:
    title: str
    steps: Tuple[RoadmapStep, ...]
    next_action: str


def compile_portfolio_roadmap(selection: PortfolioSelection, title: str = "Omega Absorb Roadmap") -> RoadmapPlan:
    steps = []
    for order, item in enumerate(selection.selected, start=1):
        if item.recommended_path == "ip_and_partner_packet":
            deliverable = "ip_partner_triage_packet"
            success_check = "risk_and_value_fields_present"
        elif item.recommended_path == "project_to_publication_packet":
            deliverable = "project_publication_seed"
            success_check = "project_tests_and_limits_present"
        elif item.recommended_path == "course_module_packet":
            deliverable = "course_module_seed"
            success_check = "concepts_exercises_rubric_present"
        else:
            deliverable = "evidence_gap_packet"
            success_check = "missing_evidence_listed"
        steps.append(
            RoadmapStep(
                order=order,
                atom_id=item.atom_id,
                path=item.recommended_path,
                score=item.score,
                deliverable=deliverable,
                success_check=success_check,
            )
        )
    return RoadmapPlan(
        title=title,
        steps=tuple(steps),
        next_action="render_roadmap_markdown",
    )


def render_roadmap_markdown(plan: RoadmapPlan) -> str:
    lines = [f"# {plan.title}", "", "## Steps"]
    for step in plan.steps:
        lines.extend(
            [
                f"### {step.order}. {step.atom_id}",
                f"- path: {step.path}",
                f"- score: {step.score:.4f}",
                f"- deliverable: {step.deliverable}",
                f"- success check: {step.success_check}",
                "",
            ]
        )
    if not plan.steps:
        lines.append("- no selected items")
    return "\n".join(lines).strip() + "\n"
