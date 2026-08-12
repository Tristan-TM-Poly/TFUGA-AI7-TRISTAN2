"""R0.2 Complexity Diff for Ω-COMPUTE-PHYSICS-T∞.

Compare two finite-domain empirical resource laws over an explicit evaluation
set. Positive/negative changes are interpreted only through a caller-selected
resource direction; no asymptotic theorem is inferred from the diff.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel, FeatureSpec

_EPS = 1e-15


@dataclass(frozen=True)
class PointDelta:
    point: Mapping[str, float]
    old_prediction: float
    new_prediction: float
    absolute_change: float
    relative_change: float
    classification: str


@dataclass(frozen=True)
class ComplexityDiffReport:
    target: str
    direction: str
    n_points: int
    mean_relative_change: float
    median_relative_change: float
    max_relative_increase: float
    max_relative_decrease: float
    regression_fraction: float
    improvement_fraction: float
    neutral_fraction: float
    domain_overlap: Mapping[str, float]
    elasticity_delta: Mapping[str, float] | None
    crossover_candidates: tuple[Mapping[str, float], ...]
    point_deltas: tuple[PointDelta, ...]
    epistemic_level: str = "finite-domain-empirical-complexity-diff"
    oak_warning: str = (
        "This report compares empirical predictions on explicit finite-domain "
        "points. It does not establish a change in mathematical Big-O/Theta "
        "complexity unless accompanied by a separate proof."
    )

    def to_dict(self, *, include_points: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_points:
            payload.pop("point_deltas", None)
        return payload


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return math.nan
    middle = n // 2
    if n % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def model_elasticity(
    model: EmpiricalResourceModel,
    point: Mapping[str, float],
    *,
    relative_step: float = 1e-4,
) -> dict[str, float]:
    """Finite-difference d log(resource) / d log(variable)."""

    factor = 1.0 + relative_step
    if factor <= 1.0:
        raise ValueError("relative_step must be positive")
    result: dict[str, float] = {}
    for variable in model.variables:
        x = float(point[variable])
        if x <= 0:
            raise ValueError("elasticity requires strictly positive coordinates")
        plus = dict(point)
        minus = dict(point)
        plus[variable] = x * factor
        minus[variable] = x / factor
        y_plus = model.predict(plus)
        y_minus = model.predict(minus)
        if y_plus <= 0 or y_minus <= 0:
            raise ValueError("elasticity requires positive model predictions")
        result[variable] = (
            math.log(y_plus) - math.log(y_minus)
        ) / (
            math.log(plus[variable]) - math.log(minus[variable])
        )
    return result


def _domain_overlap(
    old: EmpiricalResourceModel,
    new: EmpiricalResourceModel,
) -> dict[str, float]:
    result: dict[str, float] = {}
    common = sorted(set(old.domain) & set(new.domain))
    for variable in common:
        old_low, old_high = old.domain[variable]
        new_low, new_high = new.domain[variable]
        union_low = min(old_low, new_low)
        union_high = max(old_high, new_high)
        intersection_low = max(old_low, new_low)
        intersection_high = min(old_high, new_high)
        union_width = union_high - union_low
        intersection = max(0.0, intersection_high - intersection_low)
        if union_width <= _EPS:
            result[variable] = 1.0 if abs(old_low - new_low) <= _EPS else 0.0
        else:
            result[variable] = intersection / union_width
    return result


def _classification(
    relative_change: float,
    *,
    direction: str,
    tolerance: float,
) -> str:
    if abs(relative_change) <= tolerance:
        return "neutral"
    if direction == "lower-is-better":
        return "regression" if relative_change > 0 else "improvement"
    if direction == "higher-is-better":
        return "improvement" if relative_change > 0 else "regression"
    raise ValueError("direction must be 'lower-is-better' or 'higher-is-better'")


def _crossover_candidates(
    old: EmpiricalResourceModel,
    new: EmpiricalResourceModel,
    points: Sequence[Mapping[str, float]],
) -> tuple[Mapping[str, float], ...]:
    """Find sampled sign changes in new-old for a 1-D sweep.

    The output is a bounded empirical crossover bracket midpoint, not an exact
    root and not a theorem about the entire domain.
    """

    if not points or len(old.variables) != 1 or old.variables != new.variables:
        return ()
    variable = old.variables[0]
    ordered = sorted(points, key=lambda point: float(point[variable]))
    results: list[Mapping[str, float]] = []
    previous_point = ordered[0]
    previous_delta = new.predict(previous_point) - old.predict(previous_point)
    for point in ordered[1:]:
        delta = new.predict(point) - old.predict(point)
        if delta == 0.0:
            results.append({variable: float(point[variable])})
        elif previous_delta == 0.0:
            pass
        elif delta * previous_delta < 0.0:
            results.append(
                {
                    variable: 0.5
                    * (float(previous_point[variable]) + float(point[variable]))
                }
            )
        previous_point = point
        previous_delta = delta
    return tuple(results)


def compare_models(
    old: EmpiricalResourceModel,
    new: EmpiricalResourceModel,
    points: Sequence[Mapping[str, float]],
    *,
    direction: str = "lower-is-better",
    relative_tolerance: float = 0.02,
    elasticity_anchor: Mapping[str, float] | None = None,
    include_point_deltas: bool = True,
) -> ComplexityDiffReport:
    """Compare empirical resource laws over explicit points."""

    if old.target != new.target:
        raise ValueError("models must predict the same resource target")
    if not points:
        raise ValueError("Complexity Diff needs at least one evaluation point")
    if direction not in {"lower-is-better", "higher-is-better"}:
        raise ValueError("unsupported resource direction")
    if relative_tolerance < 0:
        raise ValueError("relative_tolerance cannot be negative")

    deltas: list[PointDelta] = []
    classes: list[str] = []
    relative_changes: list[float] = []
    for point in points:
        old_value = old.predict(point)
        new_value = new.predict(point)
        absolute = new_value - old_value
        relative = absolute / max(abs(old_value), _EPS)
        cls = _classification(
            relative,
            direction=direction,
            tolerance=relative_tolerance,
        )
        relative_changes.append(relative)
        classes.append(cls)
        if include_point_deltas:
            deltas.append(
                PointDelta(
                    point=dict(point),
                    old_prediction=old_value,
                    new_prediction=new_value,
                    absolute_change=absolute,
                    relative_change=relative,
                    classification=cls,
                )
            )

    n = len(points)
    elasticity_delta: Mapping[str, float] | None = None
    if elasticity_anchor is not None:
        old_e = model_elasticity(old, elasticity_anchor)
        new_e = model_elasticity(new, elasticity_anchor)
        common = sorted(set(old_e) & set(new_e))
        elasticity_delta = {name: new_e[name] - old_e[name] for name in common}

    return ComplexityDiffReport(
        target=old.target,
        direction=direction,
        n_points=n,
        mean_relative_change=sum(relative_changes) / n,
        median_relative_change=_median(relative_changes),
        max_relative_increase=max(relative_changes),
        max_relative_decrease=min(relative_changes),
        regression_fraction=classes.count("regression") / n,
        improvement_fraction=classes.count("improvement") / n,
        neutral_fraction=classes.count("neutral") / n,
        domain_overlap=_domain_overlap(old, new),
        elasticity_delta=elasticity_delta,
        crossover_candidates=_crossover_candidates(old, new, points),
        point_deltas=tuple(deltas),
    )


def model_from_serialized(payload: Mapping[str, Any]) -> EmpiricalResourceModel:
    """Rebuild an empirical model from an Atlas v0.1-compatible model payload."""

    features = tuple(
        FeatureSpec(
            kind=str(item["kind"]),
            variables=tuple(str(v) for v in item.get("variables", ())),
            powers=tuple(int(p) for p in item.get("powers", ())),
        )
        for item in payload["features"]
    )
    return EmpiricalResourceModel(
        target=str(payload["target"]),
        variables=tuple(str(v) for v in payload["variables"]),
        features=features,
        coefficients=tuple(float(v) for v in payload["coefficients"]),
        n_samples=int(payload["n_samples"]),
        domain={
            str(name): (float(bounds[0]), float(bounds[1]))
            for name, bounds in payload["domain"].items()
        },
        rmse=float(payload["rmse"]),
        r2=float(payload["r2"]),
        ridge=float(payload["ridge"]),
        status=str(payload.get("status", "empirical-fit")),
        epistemic_level=str(
            payload.get("epistemic_level", "finite-domain-empirical")
        ),
    )


def load_model_from_atlas(
    path: str | Path,
    target: str,
) -> EmpiricalResourceModel:
    """Load one resource law from a serialized Complexity Atlas JSON."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    models = payload.get("models", {})
    if target not in models:
        raise KeyError(f"target {target!r} not found in atlas models")
    return model_from_serialized(models[target])


def geometric_sweep(
    variable: str,
    start: float,
    stop: float,
    *,
    count: int = 32,
    fixed: Mapping[str, float] | None = None,
) -> list[dict[str, float]]:
    """Generate a positive logarithmic sweep for finite-domain comparison."""

    if start <= 0 or stop <= 0 or stop < start:
        raise ValueError("geometric sweep requires 0 < start <= stop")
    if count < 2:
        raise ValueError("count must be >= 2")
    fixed = dict(fixed or {})
    if start == stop:
        values = [start for _ in range(count)]
    else:
        ratio = (stop / start) ** (1.0 / (count - 1))
        values = [start * ratio**index for index in range(count)]
    return [dict(fixed, **{variable: value}) for value in values]
