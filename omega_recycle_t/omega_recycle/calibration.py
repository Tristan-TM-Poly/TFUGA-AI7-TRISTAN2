from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class ProbabilisticObservation:
    probability: float
    outcome: int
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be in [0, 1]")
        if self.outcome not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
        if self.weight <= 0:
            raise ValueError("weight must be positive")


@dataclass(frozen=True, slots=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    total_weight: float
    mean_probability: float
    event_rate: float
    absolute_gap: float


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    count: int
    total_weight: float
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    bins: tuple[ReliabilityBin, ...]
    claim_boundary: str = "calibration_metrics_only_not_causal_or_safety_validation"


def calibration_report(
    observations: tuple[ProbabilisticObservation, ...],
    *,
    bins: int = 10,
    epsilon: float = 1e-15,
) -> CalibrationReport:
    """Weighted Brier score, log loss and ECE for functional-state probabilities."""
    if not observations:
        raise ValueError("at least one observation is required")
    if bins <= 0:
        raise ValueError("bins must be positive")
    if not 0 < epsilon < 0.5:
        raise ValueError("epsilon must be in (0, 0.5)")

    total_weight = sum(obs.weight for obs in observations)
    brier = sum(obs.weight * (obs.probability - obs.outcome) ** 2 for obs in observations) / total_weight
    log_loss = 0.0
    for obs in observations:
        p = min(1.0 - epsilon, max(epsilon, obs.probability))
        log_loss += obs.weight * (-(obs.outcome * math.log(p) + (1 - obs.outcome) * math.log(1 - p)))
    log_loss /= total_weight

    buckets: list[list[ProbabilisticObservation]] = [[] for _ in range(bins)]
    for obs in observations:
        index = min(bins - 1, int(obs.probability * bins))
        buckets[index].append(obs)

    reliability: list[ReliabilityBin] = []
    ece = 0.0
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        weight = sum(obs.weight for obs in bucket)
        mean_probability = sum(obs.weight * obs.probability for obs in bucket) / weight
        event_rate = sum(obs.weight * obs.outcome for obs in bucket) / weight
        gap = abs(mean_probability - event_rate)
        ece += (weight / total_weight) * gap
        reliability.append(
            ReliabilityBin(
                lower=index / bins,
                upper=(index + 1) / bins,
                count=len(bucket),
                total_weight=weight,
                mean_probability=mean_probability,
                event_rate=event_rate,
                absolute_gap=gap,
            )
        )

    return CalibrationReport(
        count=len(observations),
        total_weight=total_weight,
        brier_score=brier,
        log_loss=log_loss,
        expected_calibration_error=ece,
        bins=tuple(reliability),
    )
