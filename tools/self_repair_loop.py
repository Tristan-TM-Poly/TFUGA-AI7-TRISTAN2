"""Self repair loop for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T.

Converts a failure into a traceable repair plan with a reproducer, test, note,
and next patch plan. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepairPlan:
    failure: str
    minimal_reproduction: str
    failing_test: str
    suspected_cause: str
    safe_patch_plan: str
    learning_note: str
    next_patch: str


def build_repair_plan(failure: str, *, module: str = "unknown") -> RepairPlan:
    safe_name = module.replace("/", "_").replace(".", "_")
    return RepairPlan(
        failure=failure,
        minimal_reproduction=f"examples/repro_{safe_name}.md",
        failing_test=f"tests/test_{safe_name}_regression.py",
        suspected_cause="document suspected cause before editing code",
        safe_patch_plan="prepare minimal patch on draft branch with regression test",
        learning_note=f"safety/m_minus_{safe_name}.yaml",
        next_patch="create regression test first, patch second",
    )
