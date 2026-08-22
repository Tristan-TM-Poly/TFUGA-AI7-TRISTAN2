"""R0.3 finite-domain inverse resource design for Ω-COMPUTE-PHYSICS-T∞.

Given empirical resource models and a bounded candidate configuration set, this
module finds feasible configurations, robustly applies optional uncertainty
radii, and computes Pareto fronts. It does not optimize outside the supplied
finite domain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel

_EPS = 1e-15


@dataclass(frozen=True)
class ResourceConstraint:
    target: str
    upper: float | None = None
    lower: float | None = None
    safety_margin: float = 0.0

    def __post_init__(self) -> None:
        if self.upper is None and self.lower is None:
            raise ValueError("constraint needs upper and/or lower bound")
        if self.upper is not None and self.lower is not None and self.lower > self.upper:
            raise ValueError("constraint lower cannot exceed upper")
        if self.safety_margin < 0:
            raise ValueError("safety_margin cannot be negative")


@dataclass(frozen=True)
class CandidateEvaluation:
    point: Mapping[str, float]
    predictions: Mapping[str, float]
    robust_predictions: Mapping[str, tuple[float, float]]
    feasible: bool
    violations: tuple[str, ...]
    objective_value: float | None
    utility: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BudgetCompileReport:
    n_candidates: int
    n_feasible: int
    objective_target: str | None
    objective_direction: str | None
    best: CandidateEvaluation | None
    evaluations: tuple[CandidateEvaluation, ...]
    epistemic_level: str = "finite-domain-empirical-inverse-design"
    oak_warning: str = (
        "The selected configuration is optimal only within the supplied candidate "
        "set and empirical model domain. Predictions and uncertainty radii do not "
        "constitute hard physical or mathematical guarantees."
    )

    def to_dict(self, *, include_evaluations: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_evaluations:
            payload.pop("evaluations", None)
        return payload


def _interval(
    prediction: float,
    *,
    uncertainty_radius: float,
) -> tuple[float, float]:
    radius = max(float(uncertainty_radius), 0.0)
    return prediction - radius, prediction + radius


def evaluate_configuration(
    models: Mapping[str, EmpiricalResourceModel],
    point: Mapping[str, float],
    *,
    constraints: Sequence[ResourceConstraint] = (),
    uncertainty_radii: Mapping[str, float] | None = None,
    objective_target: str | None = None,
    objective_direction: str = "minimize",
) -> CandidateEvaluation:
    if not models:
        raise ValueError("models cannot be empty")
    if objective_target is not None and objective_target not in models:
        raise KeyError(f"objective model {objective_target!r} missing")
    if objective_direction not in {"minimize", "maximize"}:
        raise ValueError("objective_direction must be minimize or maximize")

    uncertainty_radii = dict(uncertainty_radii or {})
    predictions = {name: model.predict(point) for name, model in models.items()}
    robust = {
        name: _interval(
            prediction,
            uncertainty_radius=uncertainty_radii.get(name, 0.0),
        )
        for name, prediction in predictions.items()
    }

    violations: list[str] = []
    for constraint in constraints:
        if constraint.target not in predictions:
            raise KeyError(f"constraint model {constraint.target!r} missing")
        low, high = robust[constraint.target]
        if constraint.upper is not None:
            allowed = float(constraint.upper) - constraint.safety_margin
            if high > allowed:
                violations.append(
                    f"{constraint.target}: robust upper {high:.6g} > {allowed:.6g}"
                )
        if constraint.lower is not None:
            allowed = float(constraint.lower) + constraint.safety_margin
            if low < allowed:
                violations.append(
                    f"{constraint.target}: robust lower {low:.6g} < {allowed:.6g}"
                )

    objective_value = None
    utility = None
    if objective_target is not None:
        objective_value = predictions[objective_target]
        utility = (
            -objective_value if objective_direction == "minimize" else objective_value
        )

    return CandidateEvaluation(
        point=dict(point),
        predictions=predictions,
        robust_predictions=robust,
        feasible=not violations,
        violations=tuple(violations),
        objective_value=objective_value,
        utility=utility,
    )


def compile_budget(
    models: Mapping[str, EmpiricalResourceModel],
    candidate_points: Sequence[Mapping[str, float]],
    *,
    constraints: Sequence[ResourceConstraint] = (),
    uncertainty_radii: Mapping[str, float] | None = None,
    objective_target: str | None = None,
    objective_direction: str = "minimize",
) -> BudgetCompileReport:
    """Find the best feasible point in a bounded candidate set."""

    if not candidate_points:
        raise ValueError("candidate_points cannot be empty")
    evaluations = tuple(
        evaluate_configuration(
            models,
            point,
            constraints=constraints,
            uncertainty_radii=uncertainty_radii,
            objective_target=objective_target,
            objective_direction=objective_direction,
        )
        for point in candidate_points
    )
    feasible = [item for item in evaluations if item.feasible]
    best = None
    if feasible:
        if objective_target is None:
            best = feasible[0]
        else:
            best = max(
                feasible,
                key=lambda item: (
                    float(item.utility),
                    tuple(sorted(item.point.items())),
                ),
            )

    return BudgetCompileReport(
        n_candidates=len(evaluations),
        n_feasible=len(feasible),
        objective_target=objective_target,
        objective_direction=objective_direction if objective_target is not None else None,
        best=best,
        evaluations=evaluations,
    )


def _dominates(
    left: CandidateEvaluation,
    right: CandidateEvaluation,
    objectives: Mapping[str, str],
    *,
    tolerance: float,
) -> bool:
    weakly_better = True
    strictly_better = False
    for target, direction in objectives.items():
        if direction not in {"minimize", "maximize"}:
            raise ValueError(f"unsupported objective direction for {target}: {direction}")
        a = left.predictions[target]
        b = right.predictions[target]
        scale = max(abs(a), abs(b), 1.0)
        eps = tolerance * scale
        if direction == "minimize":
            if a > b + eps:
                weakly_better = False
                break
            if a < b - eps:
                strictly_better = True
        else:
            if a < b - eps:
                weakly_better = False
                break
            if a > b + eps:
                strictly_better = True
    return weakly_better and strictly_better


def pareto_front(
    models: Mapping[str, EmpiricalResourceModel],
    candidate_points: Sequence[Mapping[str, float]],
    *,
    objectives: Mapping[str, str],
    constraints: Sequence[ResourceConstraint] = (),
    uncertainty_radii: Mapping[str, float] | None = None,
    tolerance: float = 1e-9,
) -> list[CandidateEvaluation]:
    """Return nondominated feasible candidates for multiple resources/quality."""

    if not objectives:
        raise ValueError("objectives cannot be empty")
    missing = sorted(set(objectives) - set(models))
    if missing:
        raise KeyError(f"missing objective models: {missing}")

    evaluations = [
        evaluate_configuration(
            models,
            point,
            constraints=constraints,
            uncertainty_radii=uncertainty_radii,
        )
        for point in candidate_points
    ]
    feasible = [item for item in evaluations if item.feasible]
    front: list[CandidateEvaluation] = []
    for candidate in feasible:
        if any(
            _dominates(other, candidate, objectives, tolerance=tolerance)
            for other in feasible
            if other is not candidate
        ):
            continue
        front.append(candidate)
    return sorted(
        front,
        key=lambda item: tuple(
            (
                item.predictions[target]
                if direction == "minimize"
                else -item.predictions[target]
            )
            for target, direction in sorted(objectives.items())
        ),
    )


def quality_per_cost(
    quality: float,
    costs: Mapping[str, float],
    *,
    weights: Mapping[str, float] | None = None,
) -> float:
    """Configurable quality/resource efficiency scalar for ranking only."""

    weights = dict(weights or {})
    denominator = 0.0
    for target, value in costs.items():
        denominator += weights.get(target, 1.0) * max(float(value), 0.0)
    return float(quality) / max(denominator, _EPS)
