from __future__ import annotations

from dataclasses import dataclass

from .models import Workflow
from .oak_gate import evaluate_workflow


CAPABILITY_DIMENSIONS = (
    "scope",
    "autonomy",
    "reversibility",
    "safety",
    "usefulness",
    "reliability",
    "cost_control",
    "learning",
    "integration",
    "value_creation",
)


@dataclass(frozen=True)
class CapacityVector:
    scope: float
    autonomy: float
    reversibility: float
    safety: float
    usefulness: float
    reliability: float
    cost_control: float
    learning: float
    integration: float
    value_creation: float

    def values(self) -> tuple[float, ...]:
        return tuple(max(0.0, min(1.0, float(getattr(self, name)))) for name in CAPABILITY_DIMENSIONS)

    def score(self) -> float:
        return round(sum(self.values()) / len(CAPABILITY_DIMENSIONS), 4)

    def to_dict(self) -> dict[str, float]:
        return {name: value for name, value in zip(CAPABILITY_DIMENSIONS, self.values(), strict=True)}


@dataclass(frozen=True)
class CapabilityAssessment:
    level: str
    vector: CapacityVector
    oak_score: float
    anti_chaos_index: float
    red_lock_violations: list[str]
    next_safe_exceed_steps: list[str]

    def can_exceed(self) -> bool:
        return self.oak_score >= 0.70 and self.anti_chaos_index >= 0.0 and not self.red_lock_violations


def infer_capacity_vector(workflow: Workflow) -> CapacityVector:
    report = evaluate_workflow(workflow)
    step_count = len(workflow.steps)
    output_count = len(workflow.outputs)
    forbidden_count = len(workflow.permissions.get("forbidden", []))
    write_count = len(workflow.permissions.get("write", []))

    return CapacityVector(
        scope=min(1.0, (step_count + output_count) / 14),
        autonomy=0.25 if workflow.trigger.get("type") == "manual" else 0.45,
        reversibility=report.reversibility,
        safety=report.safety,
        usefulness=report.usefulness,
        reliability=max(0.40, min(1.0, report.final_score)),
        cost_control=report.cost_control,
        learning=0.65 if "log_to_m_plus_m_minus" in workflow.steps else 0.45,
        integration=min(1.0, 0.25 + 0.08 * write_count),
        value_creation=min(1.0, 0.40 + 0.05 * step_count + 0.02 * forbidden_count),
    )


def capability_level(score: float) -> str:
    if score < 0.20:
        return "C0_inert"
    if score < 0.35:
        return "C1_draft"
    if score < 0.50:
        return "C2_dry_run"
    if score < 0.62:
        return "C3_local"
    if score < 0.74:
        return "C4_connected_draft"
    if score < 0.84:
        return "C5_controlled_action"
    if score < 0.92:
        return "C6_self_healing_bounded"
    return "C7_generator_or_ecosystem_candidate"


def anti_chaos_index(workflow: Workflow) -> float:
    report = evaluate_workflow(workflow)
    clarity = report.clarity
    value = report.usefulness
    reversibility = report.reversibility
    safety = report.safety
    noise_penalty = 0.03 * max(0, len(workflow.outputs) - 4)
    complexity_penalty = 0.015 * max(0, len(workflow.steps) - 10)
    blocker_penalty = 0.12 * len(report.blockers)
    warning_penalty = 0.04 * len(report.warnings)
    return round(clarity + value + reversibility + safety - noise_penalty - complexity_penalty - blocker_penalty - warning_penalty - 2.0, 4)


def assess_capability(workflow: Workflow) -> CapabilityAssessment:
    report = evaluate_workflow(workflow)
    vector = infer_capacity_vector(workflow)
    red_locks = [blocker for blocker in report.blockers if "sensitive_write_permissions" in blocker]
    steps = propose_safe_exceed_steps(workflow)
    return CapabilityAssessment(
        level=capability_level(vector.score()),
        vector=vector,
        oak_score=report.final_score,
        anti_chaos_index=anti_chaos_index(workflow),
        red_lock_violations=red_locks,
        next_safe_exceed_steps=steps,
    )


def propose_safe_exceed_steps(workflow: Workflow) -> list[str]:
    steps: list[str] = []
    if "produce_dry_run_report" not in workflow.steps:
        steps.append("add_dry_run_report")
    if "log_to_m_plus_m_minus" not in workflow.steps:
        steps.append("add_m_plus_m_minus_logging")
    if "generate_tests" not in workflow.steps:
        steps.append("add_generated_tests")
    if "measure_proof_of_workflow" not in workflow.steps:
        steps.append("add_proof_of_workflow_metrics")
    if not workflow.rollback.get("possible", False):
        steps.append("add_rollback_plan")
    if not steps:
        steps.append("increase_benchmark_coverage_without_new_permissions")
    return steps
