"""Confidence debt and empirical-evidence half-life for R0.6.

Confidence debt is an operational prioritization score. It increases with stale
measurements, calibration miss, domain mismatch, code drift and machine drift.
It is not a probability that a claim is false.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


@dataclass(frozen=True)
class ConfidenceDebtReport:
    age_days: float
    half_life_days: float
    freshness: float
    calibration_gap: float
    domain_gap: float
    code_changed: bool
    machine_changed: bool
    debt: float
    priority: str
    status: str = "empirical-confidence-debt"
    oak_warning: str = (
        "Confidence debt is a scheduling heuristic for revalidation. It is not a "
        "posterior probability, truth score or formal uncertainty guarantee."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def confidence_debt(
    *,
    age_days: float,
    half_life_days: float = 30.0,
    empirical_coverage: float = 0.90,
    nominal_coverage: float = 0.90,
    domain_overlap: float = 1.0,
    code_changed: bool = False,
    machine_changed: bool = False,
    code_change_penalty: float = 0.35,
    machine_change_penalty: float = 0.25,
) -> ConfidenceDebtReport:
    if age_days < 0:
        raise ValueError("age_days must be non-negative")
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    if not 0.0 <= empirical_coverage <= 1.0 or not 0.0 <= nominal_coverage <= 1.0:
        raise ValueError("coverage must be in [0, 1]")
    if not 0.0 <= domain_overlap <= 1.0:
        raise ValueError("domain_overlap must be in [0, 1]")
    freshness = 2.0 ** (-age_days / half_life_days)
    staleness = 1.0 - freshness
    calibration_gap = max(0.0, nominal_coverage - empirical_coverage)
    domain_gap = 1.0 - domain_overlap
    debt = (
        0.35 * staleness
        + 0.25 * calibration_gap
        + 0.20 * domain_gap
        + (code_change_penalty if code_changed else 0.0)
        + (machine_change_penalty if machine_changed else 0.0)
    )
    debt = max(0.0, min(1.0, debt))
    if debt >= 0.70:
        priority = "critical-revalidate"
    elif debt >= 0.40:
        priority = "high-revalidate"
    elif debt >= 0.20:
        priority = "schedule-revalidation"
    else:
        priority = "fresh-enough"
    return ConfidenceDebtReport(
        age_days=age_days,
        half_life_days=half_life_days,
        freshness=freshness,
        calibration_gap=calibration_gap,
        domain_gap=domain_gap,
        code_changed=code_changed,
        machine_changed=machine_changed,
        debt=debt,
        priority=priority,
    )
