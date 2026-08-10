from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .calibration import CalibrationReport, ProbabilisticObservation, calibration_report


@dataclass(frozen=True, slots=True)
class TimedProbabilisticObservation:
    timestamp: str
    probability: float
    outcome: int
    weight: float = 1.0

    def year(self) -> int:
        return datetime.fromisoformat(self.timestamp.replace("Z", "+00:00")).year


@dataclass(frozen=True, slots=True)
class CalibrationWindow:
    year: int
    report: CalibrationReport


@dataclass(frozen=True, slots=True)
class CalibrationDriftReport:
    windows: tuple[CalibrationWindow, ...]
    brier_delta_first_to_last: float
    ece_delta_first_to_last: float
    deterioration_detected: bool
    claim_boundary: str = "temporal_calibration_drift_only_not_causality_or_future_performance_guarantee"


def temporal_calibration_report(
    observations: tuple[TimedProbabilisticObservation, ...],
    *,
    bins: int = 10,
) -> CalibrationDriftReport:
    if not observations:
        raise ValueError("at least one timed observation is required")
    by_year: dict[int, list[ProbabilisticObservation]] = {}
    for item in observations:
        by_year.setdefault(item.year(), []).append(
            ProbabilisticObservation(item.probability, item.outcome, item.weight)
        )
    windows = tuple(
        CalibrationWindow(year, calibration_report(tuple(by_year[year]), bins=bins))
        for year in sorted(by_year)
    )
    first = windows[0].report
    last = windows[-1].report
    brier_delta = last.brier_score - first.brier_score
    ece_delta = last.expected_calibration_error - first.expected_calibration_error
    return CalibrationDriftReport(
        windows=windows,
        brier_delta_first_to_last=brier_delta,
        ece_delta_first_to_last=ece_delta,
        deterioration_detected=brier_delta > 1e-12 or ece_delta > 1e-12,
    )
