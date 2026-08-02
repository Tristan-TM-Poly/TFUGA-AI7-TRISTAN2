"""Residual classification and unknown-unknown radar."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from statistics import mean
from typing import Any, Mapping, Sequence


class ResidualCategory(str, Enum):
    RANDOM_NOISE = "random_noise"
    SYSTEMATIC_BIAS = "systematic_bias"
    DRIFT = "drift"
    PERIODIC = "periodic"
    STATE_DEPENDENT = "state_dependent"
    SCALE_MISMATCH = "scale_mismatch"
    VERSION_MIXTURE = "version_mixture"
    MISSING_VARIABLE = "missing_variable"
    MODEL_CLASS_FAILURE = "model_class_failure"
    INSTRUMENT_EFFECT = "instrument_effect"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ResidualRecord:
    record_id: str
    observed: tuple[float, ...]
    predicted: tuple[float, ...]
    context: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.observed) != len(self.predicted) or not self.observed:
            raise ValueError(
                "observed and predicted must align and be non-empty"
            )

    @property
    def values(self) -> tuple[float, ...]:
        return tuple(
            actual - estimate
            for actual, estimate in zip(self.observed, self.predicted)
        )

    @property
    def bias(self) -> float:
        return mean(self.values)

    @property
    def rmse(self) -> float:
        return sqrt(mean(value * value for value in self.values))

    @property
    def sign_changes(self) -> int:
        values = self.values
        return sum(
            (left < 0 < right) or (left > 0 > right)
            for left, right in zip(values, values[1:])
        )


@dataclass(frozen=True, slots=True)
class ResidualAssessment:
    category: ResidualCategory
    confidence: float
    evidence: tuple[str, ...]
    unknown_unknown_score: float


class ResidualMiner:
    def assess(self, record: ResidualRecord) -> ResidualAssessment:
        values = record.values
        count = len(values)
        scale = max(record.rmse, 1.0e-12)
        bias_ratio = abs(record.bias) / scale
        window = max(1, count // 3)
        first = mean(values[:window])
        last = mean(values[-window:])
        drift_ratio = abs(last - first) / scale
        alternating = record.sign_changes / max(1, count - 1)
        categories: list[tuple[float, ResidualCategory, str]] = [
            (
                min(1.0, bias_ratio),
                ResidualCategory.SYSTEMATIC_BIAS,
                f"bias_ratio={bias_ratio:.3f}",
            ),
            (
                min(1.0, drift_ratio / 2),
                ResidualCategory.DRIFT,
                f"drift_ratio={drift_ratio:.3f}",
            ),
            (
                alternating if alternating > 0.6 else 0.0,
                ResidualCategory.PERIODIC,
                f"sign_change_ratio={alternating:.3f}",
            ),
        ]
        if record.context.get("version_count", 1) > 1:
            categories.append(
                (
                    0.8,
                    ResidualCategory.VERSION_MIXTURE,
                    "multiple_versions_in_context",
                )
            )
        if record.context.get("instrument_changed"):
            categories.append(
                (
                    0.8,
                    ResidualCategory.INSTRUMENT_EFFECT,
                    "instrument_changed",
                )
            )
        score, category, evidence = max(
            categories,
            key=lambda item: item[0],
        )
        if record.rmse < 1.0e-9:
            return ResidualAssessment(
                ResidualCategory.RANDOM_NOISE,
                1.0,
                ("near_zero_residual",),
                0.0,
            )
        structured = max(bias_ratio, drift_ratio / 2, alternating)
        denominator = abs(mean(record.observed)) + scale
        unknown_score = min(
            1.0,
            record.rmse / denominator * (0.5 + structured),
        )
        if score < 0.25:
            category = ResidualCategory.UNKNOWN
            evidence = "no_known_signature_dominates"
            score = 0.5
        return ResidualAssessment(
            category,
            min(1.0, score),
            (evidence, f"rmse={record.rmse:.6g}"),
            unknown_score,
        )

    def batch(
        self,
        records: Sequence[ResidualRecord],
    ) -> tuple[ResidualAssessment, ...]:
        return tuple(self.assess(record) for record in records)

    def unknown_unknown_radar(
        self,
        records: Sequence[ResidualRecord],
        *,
        threshold: float = 0.35,
    ) -> tuple[str, ...]:
        flagged: list[str] = []
        for record in records:
            assessment = self.assess(record)
            if (
                assessment.unknown_unknown_score >= threshold
                or assessment.category
                in {
                    ResidualCategory.UNKNOWN,
                    ResidualCategory.MODEL_CLASS_FAILURE,
                }
            ):
                flagged.append(record.record_id)
        return tuple(flagged)
