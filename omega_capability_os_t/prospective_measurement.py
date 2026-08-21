"""Prospective measurement for Capability OS.

Criteria are frozen before an execution is scored. The court compares finite
baseline/transplant cohorts on lower-is-better engineering observables without
claiming causal identification from non-randomized data.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Iterable, Mapping

from omega_capability_os_t.core import stable_digest

METRICS = (
    "repair_iterations",
    "ci_failures",
    "persistent_changes",
    "regressions",
    "tool_calls",
    "residuals_remaining",
    "seconds_to_global_pass",
)


@dataclass(frozen=True)
class FrozenMeasurementCriteria:
    experiment_id: str
    metrics: tuple[str, ...] = METRICS
    min_baseline_cases: int = 1
    min_transplant_cases: int = 1
    require_noninferiority_all: bool = True
    require_strict_improvement: bool = True

    def digest(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True)
class ProspectiveExecutionReceipt:
    execution_id: str
    cohort: str
    criteria_digest: str
    measurements: Mapping[str, float]
    authority_widening: bool = False
    global_pass: bool = False

    def __post_init__(self) -> None:
        if self.cohort not in {"baseline", "transplant"}:
            raise ValueError("cohort must be baseline or transplant")
        for metric, value in self.measurements.items():
            if metric not in METRICS:
                raise ValueError(f"unknown metric: {metric}")
            number = float(value)
            if not isfinite(number) or number < 0.0:
                raise ValueError(f"metric {metric} must be finite and >= 0")


@dataclass(frozen=True)
class ProspectiveComparisonReport:
    baseline_count: int
    transplant_count: int
    baseline_means: Mapping[str, float]
    transplant_means: Mapping[str, float]
    deltas: Mapping[str, float]
    improved_metrics: tuple[str, ...]
    regressed_metrics: tuple[str, ...]
    decision: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PROMOTE means the supplied finite transplant cohort is non-inferior on all frozen lower-is-better metrics "
        "and strictly improves at least one when required, with no authority widening. It does not establish causal "
        "benefit, randomized equivalence, future generalization, or external action authority."
    )


def _mean(receipts: tuple[ProspectiveExecutionReceipt, ...], metric: str) -> float:
    return sum(float(item.measurements[metric]) for item in receipts) / len(receipts)


def compare_prospective_cohorts(
    criteria: FrozenMeasurementCriteria,
    receipts: Iterable[ProspectiveExecutionReceipt],
) -> ProspectiveComparisonReport:
    items = tuple(receipts)
    expected_digest = criteria.digest()
    blockers: list[str] = []
    if any(item.criteria_digest != expected_digest for item in items):
        blockers.append("criteria_digest_mismatch")
    if any(item.authority_widening for item in items):
        blockers.append("authority_widening_detected")

    baseline = tuple(item for item in items if item.cohort == "baseline")
    transplant = tuple(item for item in items if item.cohort == "transplant")
    if len(baseline) < criteria.min_baseline_cases:
        blockers.append("insufficient_baseline_cases")
    if len(transplant) < criteria.min_transplant_cases:
        blockers.append("insufficient_transplant_cases")

    for item in items:
        missing = set(criteria.metrics) - set(item.measurements)
        if missing:
            blockers.append("missing_frozen_metric")
            break

    baseline_means: dict[str, float] = {}
    transplant_means: dict[str, float] = {}
    deltas: dict[str, float] = {}
    improved: list[str] = []
    regressed: list[str] = []
    if baseline and transplant and not any(x in blockers for x in ("criteria_digest_mismatch", "missing_frozen_metric")):
        for metric in criteria.metrics:
            b = _mean(baseline, metric)
            t = _mean(transplant, metric)
            baseline_means[metric] = b
            transplant_means[metric] = t
            deltas[metric] = t - b
            if t < b:
                improved.append(metric)
            elif t > b:
                regressed.append(metric)

    if criteria.require_noninferiority_all and regressed:
        blockers.append("frozen_metric_regression")
    if criteria.require_strict_improvement and baseline and transplant and not improved:
        blockers.append("no_strict_frozen_metric_improvement")

    return ProspectiveComparisonReport(
        len(baseline), len(transplant), baseline_means, transplant_means, deltas,
        tuple(improved), tuple(regressed), "PROMOTE" if not blockers else "HOLD", tuple(sorted(set(blockers)))
    )
