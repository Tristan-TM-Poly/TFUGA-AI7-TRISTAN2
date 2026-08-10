from __future__ import annotations

from dataclasses import dataclass

from .models import WorkMetrics


def _ratio(numerator: float, denominator: float) -> float:
    return 0.0 if denominator <= 0 else numerator / denominator


@dataclass(frozen=True)
class WorkTelemetryInput:
    impacted_workunits: int
    triggered_jobs: int
    started_artifacts: int
    crystallized_artifacts: int
    validated_integrated_artifacts: int
    maintained_manual_lines: int
    wall_seconds: float
    validation_compute_seconds: float
    evidence_points: float
    queue_seconds: float
    obsolete_queue_seconds: float
    raw_work_units: int
    duplicate_work_units: int
    mean_quality: float = 1.0

    def __post_init__(self) -> None:
        integer_fields = (
            "impacted_workunits",
            "triggered_jobs",
            "started_artifacts",
            "crystallized_artifacts",
            "validated_integrated_artifacts",
            "maintained_manual_lines",
            "raw_work_units",
            "duplicate_work_units",
        )
        for name in integer_fields:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        for name in ("wall_seconds", "validation_compute_seconds", "evidence_points", "queue_seconds", "obsolete_queue_seconds"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if not 0.0 <= self.mean_quality <= 1.0:
            raise ValueError("mean_quality must be between 0 and 1")


def compute_metrics(data: WorkTelemetryInput) -> WorkMetrics:
    crystallization_debt = max(0, data.started_artifacts - data.crystallized_artifacts)
    validated_value = data.validated_integrated_artifacts * data.mean_quality
    return WorkMetrics(
        fanout_factor=_ratio(data.triggered_jobs, max(1, data.impacted_workunits)),
        closure_ratio=_ratio(data.crystallized_artifacts, max(1, data.started_artifacts)),
        crystallization_debt=crystallization_debt,
        generative_leverage=_ratio(data.validated_integrated_artifacts, max(1, data.maintained_manual_lines)),
        validated_work_power=_ratio(validated_value, data.wall_seconds),
        evidence_per_compute_second=_ratio(data.evidence_points, data.validation_compute_seconds),
        queue_waste_ratio=_ratio(data.obsolete_queue_seconds, max(data.queue_seconds, 1e-12)),
        duplicate_work_ratio=_ratio(data.duplicate_work_units, max(1, data.raw_work_units)),
    )
