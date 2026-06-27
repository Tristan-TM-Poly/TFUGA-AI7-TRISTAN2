from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .models import OAKReport, Workflow
from .oak_gate import evaluate_workflow
from .workflow_synth import forge_workflow_from_task

IssueDraftFormat = Literal["markdown", "json"]


@dataclass(frozen=True)
class IssueDraft:
    """Local-only GitHub issue draft.

    This object intentionally does not call GitHub. It prepares text that a later
    approved tool/action may use. AUTO² remains dry-run by default.
    """

    title: str
    body: str
    labels: tuple[str, ...]
    workflow: Workflow
    oak_report: OAKReport
    m_minus: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body,
            "labels": list(self.labels),
            "workflow": self.workflow.to_dict()["workflow"],
            "oak_report": self.oak_report.to_dict()["oak_report"],
            "m_minus": list(self.m_minus),
            "external_action": "none",
            "dry_run": True,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"

    def to_markdown(self) -> str:
        labels = ", ".join(self.labels) if self.labels else "none"
        return (
            f"# {self.title}\n\n"
            "## AUTO² dry-run issue draft\n\n"
            "This is a local draft only. No GitHub issue has been created by this artifact.\n\n"
            f"**Workflow:** `{self.workflow.id}`\n\n"
            f"**OAK status:** `{self.oak_report.status}`\n\n"
            f"**OAK score:** `{self.oak_report.final_score}`\n\n"
            f"**Suggested labels:** {labels}\n\n"
            "## Purpose\n\n"
            f"{self.workflow.purpose}\n\n"
            "## Steps\n\n"
            + "".join(f"- {step}\n" for step in self.workflow.steps)
            + "\n## Outputs\n\n"
            + "".join(f"- {output}\n" for output in self.workflow.outputs)
            + "\n## OAK blockers\n\n"
            + _list_or_none(self.oak_report.blockers)
            + "\n## OAK warnings\n\n"
            + _list_or_none(self.oak_report.warnings)
            + "\n## Human approval required for\n\n"
            + _list_or_none(self.oak_report.human_approval_required_for)
            + "\n## M⁻\n\n"
            + _list_or_none(self.m_minus)
            + "\n## Boundary\n\n"
            "AUTO² prepared this as a draft. It did not create an issue, send a message, publish content, spend money, change permissions, or disclose sensitive information.\n"
        )


def _list_or_none(items: list[str] | tuple[str, ...]) -> str:
    if not items:
        return "- none\n"
    return "".join(f"- {item}\n" for item in items)


def _labels_for(report: OAKReport) -> tuple[str, ...]:
    labels = ["auto2", "dry-run"]
    labels.append(f"oak-{report.status.replace('_', '-')}")
    if report.blockers:
        labels.append("blocked")
    if report.warnings:
        labels.append("needs-review")
    return tuple(dict.fromkeys(labels))


def _m_minus_for(workflow: Workflow, report: OAKReport) -> tuple[str, ...]:
    notes: list[str] = []
    if report.blockers:
        notes.append("Do not execute this workflow before OAK blockers are repaired.")
    if report.warnings:
        notes.append("Review warnings before converting this draft into a live issue.")
    if workflow.forbidden_actions():
        notes.append("Forbidden actions remain blocked unless a separate approved process overrides them.")
    notes.append("Dry-run only: no external action was performed.")
    return tuple(dict.fromkeys(notes))


def build_issue_draft(task_description: str, *, owner: str = "Tristan") -> IssueDraft:
    workflow = forge_workflow_from_task(task_description, owner=owner)
    report = evaluate_workflow(workflow)
    title = f"AUTO²: {task_description[:72]}"
    return IssueDraft(
        title=title,
        body="",
        labels=_labels_for(report),
        workflow=workflow,
        oak_report=report,
        m_minus=_m_minus_for(workflow, report),
    )


def render_issue_draft(task_description: str, *, owner: str = "Tristan", output_format: IssueDraftFormat = "markdown") -> str:
    draft = build_issue_draft(task_description, owner=owner)
    if output_format == "json":
        return draft.to_json()
    return draft.to_markdown()


def write_issue_draft(task_description: str, output_path: str | Path, *, owner: str = "Tristan", output_format: IssueDraftFormat = "markdown") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_issue_draft(task_description, owner=owner, output_format=output_format), encoding="utf-8")
    return path
