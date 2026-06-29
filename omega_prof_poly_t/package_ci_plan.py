"""Package CI plan for Omega absorb v1.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CIPipelineStep:
    name: str
    command: str
    purpose: str


@dataclass(frozen=True)
class PackageCIPlan:
    steps: Tuple[CIPipelineStep, ...]
    next_action: str


def build_package_ci_plan() -> PackageCIPlan:
    steps = (
        CIPipelineStep("unit-v19", "python -m pytest tests/test_omega_absorb_poly_prof_v19.py", "validate v1.9 package surface"),
        CIPipelineStep("demo-v19", "python examples/omega_absorb_poly_prof_v19_demo.py", "validate v1.9 demo commands"),
        CIPipelineStep("cli-version", "python -m omega_prof_poly_t.cli version", "validate console entry"),
        CIPipelineStep("docs-index", "python -m omega_prof_poly_t.cli docs-index", "validate docs lineage"),
        CIPipelineStep("oak-ledger", "python -m omega_prof_poly_t.cli oak-ledger", "validate OAK ledger rendering"),
    )
    return PackageCIPlan(steps=steps, next_action="store_ci_plan_or_generate_workflow")


def render_package_ci_plan(plan: PackageCIPlan | None = None) -> str:
    plan = plan or build_package_ci_plan()
    lines = ["# Omega Absorb CI Plan", "", "step | command | purpose", "--- | --- | ---"]
    for step in plan.steps:
        lines.append(f"{step.name} | `{step.command}` | {step.purpose}")
    return "\n".join(lines) + "\n"
