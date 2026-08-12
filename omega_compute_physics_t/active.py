"""R0.3 active benchmarking for Ω-COMPUTE-PHYSICS-T∞.

The planner ranks bounded candidate experiments by an explicit information
proxy: model disagreement + geometric novelty, optionally divided by predicted
measurement cost. It does not claim exact Bayesian information gain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
import math
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel, ResourceSample

_EPS = 1e-15


@dataclass(frozen=True)
class ExperimentCandidate:
    point: Mapping[str, float]
    disagreement: float
    novelty: float
    information_proxy: float
    predicted_cost: float
    score: float
    model_predictions: tuple[float, ...]
    oak_warning: str = (
        "The ranking score is an active-learning heuristic, not exact expected "
        "information gain and not evidence that the selected point is globally optimal."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def geometric_design_space(
    bounds: Mapping[str, tuple[float, float]],
    *,
    levels: int = 5,
    max_points: int = 4096,
) -> list[dict[str, float]]:
    """Generate a bounded logarithmic Cartesian design space.

    All coordinates must be positive. The explicit max_points gate prevents
    accidental combinatorial benchmark explosions.
    """

    if levels < 2:
        raise ValueError("levels must be >= 2")
    names = tuple(sorted(bounds))
    if not names:
        raise ValueError("bounds cannot be empty")
    if levels ** len(names) > max_points:
        raise ValueError(
            f"design would contain {levels ** len(names)} points; "
            f"max_points={max_points}"
        )
    axes: list[list[float]] = []
    for name in names:
        low, high = bounds[name]
        low = float(low)
        high = float(high)
        if low <= 0 or high <= 0 or high < low:
            raise ValueError(f"{name}: require 0 < low <= high")
        if low == high:
            axes.append([low for _ in range(levels)])
        else:
            ratio = (high / low) ** (1.0 / (levels - 1))
            axes.append([low * ratio**index for index in range(levels)])
    return [
        {name: value for name, value in zip(names, values)}
        for values in product(*axes)
    ]


def _prediction_disagreement(
    predictions: Sequence[float],
) -> float:
    if len(predictions) < 2:
        return 0.0
    mean = sum(predictions) / len(predictions)
    variance = sum((value - mean) ** 2 for value in predictions) / len(predictions)
    scale = max(abs(mean), math.sqrt(variance), _EPS)
    return math.sqrt(variance) / scale


def _coordinate_scales(
    existing: Sequence[Mapping[str, float]],
    candidates: Sequence[Mapping[str, float]],
    variables: Sequence[str],
) -> dict[str, float]:
    scales: dict[str, float] = {}
    for variable in variables:
        values = [
            math.log(float(point[variable]))
            for point in tuple(existing) + tuple(candidates)
            if float(point[variable]) > 0
        ]
        if not values:
            raise ValueError("active benchmarking requires positive coordinates")
        width = max(values) - min(values)
        scales[variable] = max(width, 1.0)
    return scales


def _novelty(
    point: Mapping[str, float],
    existing: Sequence[Mapping[str, float]],
    variables: Sequence[str],
    scales: Mapping[str, float],
) -> float:
    if not existing:
        return 1.0
    best = math.inf
    for prior in existing:
        distance2 = 0.0
        for variable in variables:
            x = float(point[variable])
            y = float(prior[variable])
            if x <= 0 or y <= 0:
                raise ValueError("active benchmarking requires positive coordinates")
            delta = (math.log(x) - math.log(y)) / scales[variable]
            distance2 += delta * delta
        best = min(best, math.sqrt(distance2))
    return 1.0 - math.exp(-best)


def rank_experiments(
    models: Sequence[EmpiricalResourceModel],
    candidate_points: Sequence[Mapping[str, float]],
    *,
    existing_samples: Sequence[ResourceSample] = (),
    cost_model: EmpiricalResourceModel | None = None,
    disagreement_weight: float = 1.0,
    novelty_weight: float = 0.5,
    cost_power: float = 1.0,
) -> list[ExperimentCandidate]:
    """Rank candidate measurements by uncertainty/novelty per predicted cost."""

    if not models:
        raise ValueError("at least one empirical model is required")
    if not candidate_points:
        return []
    variables = models[0].variables
    if any(model.variables != variables for model in models):
        raise ValueError("all models must use the same variable tuple")
    existing_points = [sample.variables for sample in existing_samples]
    scales = _coordinate_scales(existing_points, candidate_points, variables)

    ranked: list[ExperimentCandidate] = []
    for point in candidate_points:
        predictions = tuple(model.predict(point) for model in models)
        disagreement = _prediction_disagreement(predictions)
        novelty = _novelty(point, existing_points, variables, scales)
        info = disagreement_weight * disagreement + novelty_weight * novelty
        predicted_cost = 1.0
        if cost_model is not None:
            predicted_cost = max(abs(cost_model.predict(point)), _EPS)
        score = info / (predicted_cost ** max(cost_power, 0.0))
        ranked.append(
            ExperimentCandidate(
                point=dict(point),
                disagreement=disagreement,
                novelty=novelty,
                information_proxy=info,
                predicted_cost=predicted_cost,
                score=score,
                model_predictions=predictions,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (
            -item.score,
            -item.disagreement,
            -item.novelty,
            tuple(sorted(item.point.items())),
        ),
    )


def select_next_experiments(
    models: Sequence[EmpiricalResourceModel],
    candidate_points: Sequence[Mapping[str, float]],
    *,
    existing_samples: Sequence[ResourceSample] = (),
    cost_model: EmpiricalResourceModel | None = None,
    count: int = 1,
    min_log_distance: float = 0.0,
    disagreement_weight: float = 1.0,
    novelty_weight: float = 0.5,
    cost_power: float = 1.0,
) -> list[ExperimentCandidate]:
    """Select a diverse top-k active benchmark batch.

    ``min_log_distance`` is a simple batch-diversity gate. The planner remains
    bounded and deterministic for a fixed candidate set.
    """

    if count < 1:
        raise ValueError("count must be >= 1")
    ranked = rank_experiments(
        models,
        candidate_points,
        existing_samples=existing_samples,
        cost_model=cost_model,
        disagreement_weight=disagreement_weight,
        novelty_weight=novelty_weight,
        cost_power=cost_power,
    )
    chosen: list[ExperimentCandidate] = []
    for candidate in ranked:
        if len(chosen) >= count:
            break
        if min_log_distance > 0 and chosen:
            too_close = False
            for previous in chosen:
                distance2 = 0.0
                for variable in models[0].variables:
                    x = float(candidate.point[variable])
                    y = float(previous.point[variable])
                    if x <= 0 or y <= 0:
                        raise ValueError("batch diversity requires positive coordinates")
                    distance2 += (math.log(x) - math.log(y)) ** 2
                if math.sqrt(distance2) < min_log_distance:
                    too_close = True
                    break
            if too_close:
                continue
        chosen.append(candidate)
    return chosen


def discriminating_experiment(
    first: EmpiricalResourceModel,
    second: EmpiricalResourceModel,
    candidate_points: Sequence[Mapping[str, float]],
    *,
    cost_model: EmpiricalResourceModel | None = None,
) -> ExperimentCandidate:
    """Choose the point where two hypotheses differ most per predicted cost."""

    ranked = rank_experiments(
        (first, second),
        candidate_points,
        cost_model=cost_model,
        disagreement_weight=1.0,
        novelty_weight=0.0,
        cost_power=1.0,
    )
    if not ranked:
        raise ValueError("no candidate points")
    return ranked[0]
