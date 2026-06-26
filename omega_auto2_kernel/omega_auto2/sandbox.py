from __future__ import annotations

from dataclasses import dataclass

from .models import Workflow
from .oak_gate import evaluate_workflow


@dataclass(frozen=True)
class DryRunReport:
    workflow_id: str
    ok: bool
    planned_steps: list[str]
    notes: list[str]
    estimated_cost_units: float

    def to_dict(self) -> dict[str, object]:
        return {
            "workflow_id": self.workflow_id,
            "ok": self.ok,
            "planned_steps": self.planned_steps,
            "notes": self.notes,
            "estimated_cost_units": self.estimated_cost_units,
        }


def dry_run_workflow(workflow: Workflow) -> DryRunReport:
    """Return a no-effect preview for a workflow."""

    report = evaluate_workflow(workflow)
    notes = list(report.blockers) + list(report.warnings)
    cost = round(0.01 * len(workflow.steps) + 0.02 * len(workflow.outputs), 4)
    return DryRunReport(
        workflow_id=workflow.id,
        ok=report.status != "blocked" and report.final_score >= 0.70,
        planned_steps=list(workflow.steps),
        notes=notes,
        estimated_cost_units=cost,
    )
