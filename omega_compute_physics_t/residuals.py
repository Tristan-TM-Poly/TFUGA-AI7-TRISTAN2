"""Residual intelligence and missing-variable proposals for Ω-META-COMPUTE-PHYSICS-T∞.

Residual structure is treated as evidence of model inadequacy or unmodelled
state, not as proof that any correlated variable is causal.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import mean
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel, ResourceSample

_EPS = 1e-15


@dataclass(frozen=True)
class ResidualPoint:
    variables: Mapping[str, float]
    predicted: float
    observed: float
    residual: float
    relative_residual: float
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class MissingVariableCandidate:
    name: str
    source: str
    correlation_with_residual: float
    absolute_correlation: float
    n: int
    status: str = "association-candidate"
    oak_warning: str = (
        "Residual association is not causal identification. The candidate must "
        "be intervened on or independently validated before causal promotion."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResidualReport:
    target: str
    n: int
    mean_residual: float
    rmse: float
    mean_absolute_relative_residual: float
    candidates: tuple[MissingVariableCandidate, ...]
    structured_residuals_detected: bool
    status: str = "residual-physics-candidate"
    oak_warning: str = (
        "Structured residuals indicate predictive mismatch or omitted structure; "
        "they do not identify a unique mechanism."
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidates"] = [row.to_dict() for row in self.candidates]
        return payload


def residual_points(
    model: EmpiricalResourceModel,
    samples: Sequence[ResourceSample],
    target: str,
) -> tuple[ResidualPoint, ...]:
    rows: list[ResidualPoint] = []
    for sample in samples:
        observed = float(sample.resources[target])
        predicted = float(model.predict(sample.variables))
        residual = observed - predicted
        scale = max(abs(observed), abs(predicted), _EPS)
        rows.append(
            ResidualPoint(
                variables=dict(sample.variables),
                predicted=predicted,
                observed=observed,
                residual=residual,
                relative_residual=residual / scale,
                metadata=dict(sample.metadata),
            )
        )
    return tuple(rows)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 3:
        return math.nan
    mx = mean(xs)
    my = mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denominator = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    if denominator <= _EPS:
        return 0.0
    return sum(a * b for a, b in zip(dx, dy)) / denominator


def _numeric_metadata_columns(points: Sequence[ResidualPoint]) -> dict[str, list[float]]:
    keys: set[str] = set()
    for point in points:
        for key, value in point.metadata.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                keys.add(str(key))
    columns: dict[str, list[float]] = {}
    for key in sorted(keys):
        values: list[float] = []
        complete = True
        for point in points:
            value = point.metadata.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                complete = False
                break
            value = float(value)
            if not math.isfinite(value):
                complete = False
                break
            values.append(value)
        if complete:
            columns[key] = values
    return columns


def discover_missing_variable_candidates(
    model: EmpiricalResourceModel,
    samples: Sequence[ResourceSample],
    target: str,
    *,
    extra_signals: Mapping[str, Sequence[float]] | None = None,
    min_absolute_correlation: float = 0.45,
) -> ResidualReport:
    """Rank numeric metadata/extra signals associated with model residuals."""

    if len(samples) < 6:
        raise ValueError("residual discovery requires at least 6 samples")
    points = residual_points(model, samples, target)
    residuals = [point.residual for point in points]
    candidates: list[MissingVariableCandidate] = []

    signals: list[tuple[str, str, Sequence[float]]] = [
        (name, "metadata", values)
        for name, values in _numeric_metadata_columns(points).items()
    ]
    for name, values in (extra_signals or {}).items():
        if len(values) != len(points):
            raise ValueError(f"extra signal {name!r} length does not match samples")
        signals.append((str(name), "extra_signal", [float(value) for value in values]))

    for name, source, values in signals:
        correlation = _pearson(values, residuals)
        if math.isnan(correlation):
            continue
        if abs(correlation) >= min_absolute_correlation:
            candidates.append(
                MissingVariableCandidate(
                    name=name,
                    source=source,
                    correlation_with_residual=correlation,
                    absolute_correlation=abs(correlation),
                    n=len(points),
                )
            )

    candidates.sort(key=lambda row: (-row.absolute_correlation, row.name))
    rmse = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    mar = sum(abs(point.relative_residual) for point in points) / len(points)
    return ResidualReport(
        target=target,
        n=len(points),
        mean_residual=mean(residuals),
        rmse=rmse,
        mean_absolute_relative_residual=mar,
        candidates=tuple(candidates),
        structured_residuals_detected=bool(candidates),
    )
