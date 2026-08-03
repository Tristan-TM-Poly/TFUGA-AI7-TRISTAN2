from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from typing import Any, Iterable

from .evidence_ladder import TIER_INDEX

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class MetricObservation:
    observation_id: str
    tier: str
    metric: str
    value: float
    unit: str
    standard_uncertainty: float
    artifact_sha256: str
    provenance: str

    def validate(self) -> None:
        if not self.observation_id.strip() or not self.metric.strip() or not self.unit.strip() or not self.provenance.strip():
            raise ValueError("observation identity, metric, unit and provenance are required")
        if self.tier not in TIER_INDEX:
            raise ValueError(f"unknown evidence tier: {self.tier}")
        if not isfinite(self.value) or not isfinite(self.standard_uncertainty) or self.standard_uncertainty < 0:
            raise ValueError("value must be finite and uncertainty finite and non-negative")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ValueError("artifact_sha256 must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscrepancyRecord:
    metric: str
    unit: str
    lower_observation_id: str
    higher_observation_id: str
    lower_tier: str
    higher_tier: str
    signed_delta: float
    absolute_delta: float
    relative_delta: float
    combined_standard_uncertainty: float
    normalized_residual: float | None
    exceeds_two_sigma: bool | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscrepancyTensorReport:
    observations: tuple[MetricObservation, ...]
    comparisons: tuple[DiscrepancyRecord, ...]
    metric_count: int
    comparison_count: int
    maximum_absolute_normalized_residual: float | None
    evidence_hash: str
    physics_certified: bool = False
    automatic_model_promotion: bool = False
    notice: str = (
        "a small discrepancy does not prove correctness and a large discrepancy does not identify "
        "which tier is wrong; provenance, uncertainty, model form and experiment quality remain required"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observations": [item.to_dict() for item in self.observations],
            "comparisons": [item.to_dict() for item in self.comparisons],
            "metric_count": self.metric_count,
            "comparison_count": self.comparison_count,
            "maximum_absolute_normalized_residual": self.maximum_absolute_normalized_residual,
            "evidence_hash": self.evidence_hash,
            "physics_certified": self.physics_certified,
            "automatic_model_promotion": self.automatic_model_promotion,
            "notice": self.notice,
        }


def build_discrepancy_tensor(observations: Iterable[MetricObservation]) -> DiscrepancyTensorReport:
    items = tuple(observations)
    ids = [item.observation_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("observation_id values must be unique")
    for item in items:
        item.validate()

    grouped: dict[tuple[str, str], list[MetricObservation]] = {}
    units_by_metric: dict[str, set[str]] = {}
    for item in items:
        units_by_metric.setdefault(item.metric, set()).add(item.unit)
        grouped.setdefault((item.metric, item.unit), []).append(item)
    mismatched = sorted(metric for metric, units in units_by_metric.items() if len(units) > 1)
    if mismatched:
        raise ValueError(f"unit mismatch for metrics: {', '.join(mismatched)}")

    comparisons: list[DiscrepancyRecord] = []
    for (metric, unit), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda item: (TIER_INDEX[item.tier], item.observation_id))
        for lower, higher in zip(ordered, ordered[1:]):
            delta = higher.value - lower.value
            combined = sqrt(lower.standard_uncertainty**2 + higher.standard_uncertainty**2)
            normalized = delta / combined if combined > 1e-15 else None
            comparisons.append(
                DiscrepancyRecord(
                    metric=metric,
                    unit=unit,
                    lower_observation_id=lower.observation_id,
                    higher_observation_id=higher.observation_id,
                    lower_tier=lower.tier,
                    higher_tier=higher.tier,
                    signed_delta=delta,
                    absolute_delta=abs(delta),
                    relative_delta=delta / max(abs(lower.value), 1e-12),
                    combined_standard_uncertainty=combined,
                    normalized_residual=normalized,
                    exceeds_two_sigma=None if normalized is None else abs(normalized) > 2.0,
                )
            )

    normalized_values = [abs(item.normalized_residual) for item in comparisons if item.normalized_residual is not None]
    stable = {
        "observations": [item.to_dict() for item in items],
        "comparisons": [item.to_dict() for item in comparisons],
    }
    return DiscrepancyTensorReport(
        observations=items,
        comparisons=tuple(comparisons),
        metric_count=len(units_by_metric),
        comparison_count=len(comparisons),
        maximum_absolute_normalized_residual=max(normalized_values) if normalized_values else None,
        evidence_hash=_digest(stable),
    )


def demo_discrepancy_tensor() -> DiscrepancyTensorReport:
    observations = (
        MetricObservation("thrust-f0", "F0_ANALYTIC", "thrust", 109.6, "N", 5.0, "1" * 64, "annular BEM demo"),
        MetricObservation("thrust-f3", "F3_VORTEX_PROXY", "thrust", 107.2, "N", 4.0, "2" * 64, "WakeGraph proxy demo"),
        MetricObservation("power-f0", "F0_ANALYTIC", "shaft_power", 3271.0, "W", 160.0, "3" * 64, "annular BEM demo"),
        MetricObservation("power-f3", "F3_VORTEX_PROXY", "shaft_power", 3340.0, "W", 180.0, "4" * 64, "WakeGraph proxy demo"),
    )
    return build_discrepancy_tensor(observations)
