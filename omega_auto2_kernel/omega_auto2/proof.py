from __future__ import annotations

from dataclasses import dataclass

from .capabilities import assess_capability
from .models import Workflow
from .oak_gate import evaluate_workflow
from .telemetry import TelemetrySnapshot


@dataclass(frozen=True)
class ProofOfWorkflow:
    workflow_id: str
    oak_score: float
    capacity_score: float
    value_score: float
    anti_chaos_index: float
    proven: bool

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def prove_workflow(workflow: Workflow, telemetry: TelemetrySnapshot) -> ProofOfWorkflow:
    oak = evaluate_workflow(workflow)
    cap = assess_capability(workflow)
    value = telemetry.value_score()
    proven = (
        oak.final_score >= 0.70
        and cap.vector.score() >= 0.45
        and cap.anti_chaos_index >= 0.0
        and value >= 0.35
    )
    return ProofOfWorkflow(
        workflow_id=workflow.id,
        oak_score=oak.final_score,
        capacity_score=cap.vector.score(),
        value_score=value,
        anti_chaos_index=cap.anti_chaos_index,
        proven=proven,
    )
