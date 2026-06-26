from __future__ import annotations

from dataclasses import dataclass

from .capabilities import assess_capability
from .models import Workflow
from .proof import prove_workflow
from .sandbox import dry_run_workflow
from .telemetry import TelemetrySnapshot


@dataclass(frozen=True)
class BenchResult:
    workflow_id: str
    passed: bool
    capacity_score: float
    proof_score: float
    dry_run_ok: bool
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def run_bench(workflow: Workflow, telemetry: TelemetrySnapshot | None = None) -> BenchResult:
    telemetry = telemetry or TelemetrySnapshot()
    capability = assess_capability(workflow)
    preview = dry_run_workflow(workflow)
    proof = prove_workflow(workflow, telemetry)
    notes = list(preview.notes)
    passed = preview.ok and capability.vector.score() >= 0.40 and capability.anti_chaos_index >= 0.0
    return BenchResult(
        workflow_id=workflow.id,
        passed=passed,
        capacity_score=capability.vector.score(),
        proof_score=proof.value_score,
        dry_run_ok=preview.ok,
        notes=notes,
    )


def run_suite(workflows: list[Workflow], telemetry: TelemetrySnapshot | None = None) -> dict[str, object]:
    results = [run_bench(workflow, telemetry).to_dict() for workflow in workflows]
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "results": results,
    }
