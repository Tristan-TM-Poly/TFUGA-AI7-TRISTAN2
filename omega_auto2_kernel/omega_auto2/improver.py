from __future__ import annotations

from dataclasses import replace

from .capabilities import propose_safe_exceed_steps
from .models import Workflow


def improve_draft(workflow: Workflow) -> Workflow:
    """Return an enriched draft with more validation steps.

    No action is executed. The function only returns a modified object.
    """

    steps = list(workflow.steps)
    for item in propose_safe_exceed_steps(workflow):
        if item not in steps:
            steps.append(item)
    return replace(workflow, steps=steps, status="draft")
