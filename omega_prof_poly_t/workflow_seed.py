"""Workflow seed for Omega Absorb OS v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WorkflowSeedStep:
    name: str
    command: str
    purpose: str


@dataclass(frozen=True)
class WorkflowSeed:
    name: str
    steps: Tuple[WorkflowSeedStep, ...]
    next_action: str


def build_workflow_seed() -> WorkflowSeed:
    steps = (
        WorkflowSeedStep("install", "python -m pip install -e .", "install package locally"),
        WorkflowSeedStep("tests", "python -m pytest", "run test suite"),
        WorkflowSeedStep("demo", "python examples/omega_absorb_poly_prof_v20_demo.py", "run v2 demo"),
        WorkflowSeedStep("reports", "python -m omega_prof_poly_t.cli write-reports", "write local reports"),
        WorkflowSeedStep("ci-plan", "python -m omega_prof_poly_t.cli ci-plan", "print CI plan"),
    )
    return WorkflowSeed("omega-absorb-v2-local-ci", steps, "write_workflow_yaml_seed")


def render_workflow_seed(seed: WorkflowSeed | None = None) -> str:
    seed = seed or build_workflow_seed()
    lines = [f"# Workflow Seed: {seed.name}", "", "step | command | purpose", "--- | --- | ---"]
    for step in seed.steps:
        lines.append(f"{step.name} | `{step.command}` | {step.purpose}")
    return "\n".join(lines) + "\n"
