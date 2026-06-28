"""Department bridge report renderer for Omega absorb v0.9."""

from __future__ import annotations

from dataclasses import dataclass

from .department_bridge_scoring import DepartmentBridgeScore


@dataclass(frozen=True)
class DepartmentBridgeReport:
    markdown: str
    score: float
    next_action: str


def render_department_bridge_report(score: DepartmentBridgeScore) -> DepartmentBridgeReport:
    lines = [
        "# Department Bridge Report",
        "",
        f"Score: {score.score:.4f}",
        "",
        "## Departments",
    ]
    lines.extend(f"- {dept}" for dept in score.departments or ("none",))
    lines.extend(
        [
            "",
            "## Counts",
            f"- professors: {score.professor_count}",
            f"- keywords: {score.keyword_count}",
            f"- methods: {score.method_count}",
            "",
            "## Next action",
            score.next_action,
        ]
    )
    return DepartmentBridgeReport(
        markdown="\n".join(lines).strip() + "\n",
        score=score.score,
        next_action="store_department_bridge_report",
    )
