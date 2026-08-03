from __future__ import annotations

from statistics import fmean
from typing import Sequence

from .models import ObservationView, PlateauKind, PlateauReport


def detect_plateau(
    observations: Sequence[ObservationView],
    window: int = 8,
) -> PlateauReport:
    if window < 2:
        raise ValueError("window must be at least 2")
    if len(observations) < window:
        return PlateauReport(
            kind=PlateauKind.NONE,
            detected=False,
            recent_window=min(window, len(observations)),
            recent_novelty=_mean([item.novelty for item in observations]),
            recent_information_gain=_mean(
                [item.information_gain for item in observations]
            ),
            recent_efficiency=_efficiency(observations),
            previous_efficiency=0.0,
            reason="insufficient_history",
        )

    recent = observations[-window:]
    previous = observations[-2 * window : -window]
    novelty = _mean([item.novelty for item in recent])
    information = _mean([item.information_gain for item in recent])
    recent_efficiency = _efficiency(recent)
    previous_efficiency = _efficiency(previous)

    if novelty <= 0.05:
        kind = PlateauKind.NOVELTY
        reason = "recent experiments add almost no new addresses"
    elif information <= 0.05:
        kind = PlateauKind.INFORMATION
        reason = "recent experiments produce little measured information"
    elif previous and recent_efficiency <= 0.6 * previous_efficiency:
        kind = PlateauKind.EFFICIENCY
        reason = "information gained per cost declined by at least forty percent"
    else:
        recent_success = _mean([1.0 if item.success else 0.0 for item in recent])
        previous_success = _mean([1.0 if item.success else 0.0 for item in previous])
        if previous and abs(recent_success - previous_success) <= 0.02:
            kind = PlateauKind.MASTERY
            reason = "empirical mastery changed by at most two percentage points"
        else:
            kind = PlateauKind.NONE
            reason = "no plateau threshold crossed"

    return PlateauReport(
        kind=kind,
        detected=kind is not PlateauKind.NONE,
        recent_window=window,
        recent_novelty=novelty,
        recent_information_gain=information,
        recent_efficiency=recent_efficiency,
        previous_efficiency=previous_efficiency,
        reason=reason,
    )


def _mean(values: Sequence[float]) -> float:
    return fmean(values) if values else 0.0


def _efficiency(observations: Sequence[ObservationView]) -> float:
    gain = sum(item.information_gain for item in observations)
    cost = sum(item.cost_units for item in observations)
    return gain / max(1, cost)
