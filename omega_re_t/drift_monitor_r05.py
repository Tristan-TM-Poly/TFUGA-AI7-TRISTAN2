"""Deterministic distribution and calibration drift evidence."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


def _normalise(values: Mapping[str, float], epsilon: float = 1.0e-12) -> dict[str, float]:
    keys = sorted(values)
    if not keys:
        raise ValueError("distribution cannot be empty")
    checked = {key: float(values[key]) for key in keys}
    if any(not math.isfinite(value) or value < 0.0 for value in checked.values()):
        raise ValueError("distribution values must be finite and non-negative")
    total = sum(checked.values())
    if total <= 0.0:
        raise ValueError("distribution must have positive mass")
    raw = {key: max(epsilon, value / total) for key, value in checked.items()}
    renormalised = sum(raw.values())
    return {key: value / renormalised for key, value in raw.items()}


def jensen_shannon(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    support = sorted(set(left) | set(right))
    p = _normalise({key: left.get(key, 0.0) for key in support})
    q = _normalise({key: right.get(key, 0.0) for key in support})
    midpoint = {key: 0.5 * (p[key] + q[key]) for key in support}

    def kl(source: Mapping[str, float], target: Mapping[str, float]) -> float:
        return sum(source[key] * math.log2(source[key] / target[key]) for key in support)

    return 0.5 * kl(p, midpoint) + 0.5 * kl(q, midpoint)


def population_stability_index(reference: Mapping[str, float], current: Mapping[str, float]) -> float:
    support = sorted(set(reference) | set(current))
    p = _normalise({key: reference.get(key, 0.0) for key in support})
    q = _normalise({key: current.get(key, 0.0) for key in support})
    return sum((q[key] - p[key]) * math.log(q[key] / p[key]) for key in support)


@dataclass(frozen=True)
class CalibrationSnapshot:
    window_id: str
    distribution: Mapping[str, float]
    brier_score: float
    expected_calibration_error: float
    executed_cases: int
    scientifically_verified_cases: int = 0

    def __post_init__(self) -> None:
        if not self.window_id.strip() or self.executed_cases <= 0:
            raise ValueError("invalid snapshot identity")
        for value in (self.brier_score, self.expected_calibration_error):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("metrics must be finite and non-negative")
        if self.scientifically_verified_cases != 0:
            raise ValueError("software snapshot cannot claim scientific verification")


@dataclass(frozen=True)
class DriftReport:
    reference_window: str
    current_window: str
    jensen_shannon_bits: float
    population_stability_index: float
    brier_delta: float
    calibration_error_delta: float
    severity: str
    reasons: tuple[str, ...]
    claim: str = "software_drift_monitoring_only"


def compare_snapshots(
    reference: CalibrationSnapshot,
    current: CalibrationSnapshot,
    *,
    js_warn: float = 0.05,
    js_block: float = 0.2,
    ece_warn: float = 0.03,
    ece_block: float = 0.1,
) -> DriftReport:
    js = jensen_shannon(reference.distribution, current.distribution)
    psi = population_stability_index(reference.distribution, current.distribution)
    brier_delta = current.brier_score - reference.brier_score
    ece_delta = current.expected_calibration_error - reference.expected_calibration_error
    reasons: list[str] = []
    severity = "stable"
    if js >= js_block or ece_delta >= ece_block:
        severity = "block"
    elif js >= js_warn or ece_delta >= ece_warn:
        severity = "review"
    if js >= js_warn:
        reasons.append("distribution_shift")
    if ece_delta >= ece_warn:
        reasons.append("calibration_degraded")
    if brier_delta > 0.0:
        reasons.append("brier_degraded")
    return DriftReport(
        reference_window=reference.window_id,
        current_window=current.window_id,
        jensen_shannon_bits=js,
        population_stability_index=psi,
        brier_delta=brier_delta,
        calibration_error_delta=ece_delta,
        severity=severity,
        reasons=tuple(reasons),
    )


def monitor_sequence(snapshots: Sequence[CalibrationSnapshot]) -> tuple[DriftReport, ...]:
    if len(snapshots) < 2:
        raise ValueError("at least two snapshots are required")
    return tuple(compare_snapshots(left, right) for left, right in zip(snapshots, snapshots[1:]))
