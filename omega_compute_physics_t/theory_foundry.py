"""Theory competition and self-falsification candidates for Ω-META-COMPUTE-PHYSICS-T∞.

A "theory" here means an empirical representation + finite-domain predictor.
It is not a mathematical theorem. The foundry keeps multiple candidates alive,
compares predictive utility and description cost, and proposes measurements
where surviving theories disagree most.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence

from .atlas import ResourceSample
from .representation import DerivedCoordinate, generate_coordinate_candidates, transform_samples
from .validation import ValidatedResourceModel, fit_validated_resource_model

_EPS = 1e-15


@dataclass(frozen=True)
class TheoryCandidate:
    name: str
    representation: DerivedCoordinate | None
    validated: ValidatedResourceModel
    cv_rmse: float
    mdl_proxy: float
    description_cost: float
    score: float
    status: str = "empirical-theory-candidate"
    oak_warning: str = (
        "This object ranks finite-domain empirical models. It is not a proof of "
        "asymptotic complexity, causality, uniqueness, or universality."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "representation": None if self.representation is None else asdict(self.representation),
            "validation": self.validated.certificate(),
            "cv_rmse": self.cv_rmse,
            "mdl_proxy": self.mdl_proxy,
            "description_cost": self.description_cost,
            "score": self.score,
            "status": self.status,
            "oak_warning": self.oak_warning,
        }


@dataclass(frozen=True)
class FalsificationCandidate:
    point: Mapping[str, float]
    disagreement: float
    relative_disagreement: float
    extrapolation_count: int
    score: float
    status: str = "counterexample-search-candidate"
    oak_warning: str = (
        "High model disagreement identifies a useful measurement candidate; it "
        "is not itself a counterexample until the system is actually measured."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _selected_score(validated: ValidatedResourceModel) -> tuple[float, float]:
    selected = validated.report.selected_candidate
    rows = [score for score in validated.report.scores if score.name == selected and score.valid]
    if not rows:
        raise ValueError(f"selected candidate {selected!r} has no valid score row")
    row = rows[0]
    return float(row.cv_rmse), float(row.mdl_proxy)


def _fit_theory(
    samples: Sequence[ResourceSample],
    target: str,
    representation: DerivedCoordinate | None,
    *,
    seed: int,
) -> ValidatedResourceModel:
    projected = list(samples) if representation is None else transform_samples(samples, representation)
    return fit_validated_resource_model(projected, target, seed=seed)


def generate_theory_competition(
    samples: Sequence[ResourceSample],
    target: str,
    *,
    max_representations: int = 24,
    description_penalty: float = 0.01,
    seed: int = 0,
) -> tuple[TheoryCandidate, ...]:
    """Generate and rank competing empirical theories.

    The original coordinates are retained as a baseline. Generated theories use
    a single derived coordinate, intentionally favouring compact explanations.
    """

    if len(samples) < 8:
        raise ValueError("theory competition requires at least 8 samples")
    variables = tuple(sorted(samples[0].variables))
    representations = generate_coordinate_candidates(
        variables,
        max_candidates=max_representations,
    )
    raw: list[tuple[str, DerivedCoordinate | None, ValidatedResourceModel, float, float, float]] = []

    try:
        baseline = _fit_theory(samples, target, None, seed=seed)
        cv, mdl = _selected_score(baseline)
        raw.append(("original", None, baseline, cv, mdl, 1.0))
    except (ValueError, KeyError, OverflowError, ZeroDivisionError):
        pass

    for index, representation in enumerate(representations):
        try:
            fitted = _fit_theory(samples, target, representation, seed=seed + index + 1)
            cv, mdl = _selected_score(fitted)
            raw.append((representation.label, representation, fitted, cv, mdl, representation.complexity_cost))
        except (ValueError, KeyError, OverflowError, ZeroDivisionError):
            continue

    if not raw:
        raise ValueError("all generated theories failed")
    finite_cv = [cv for _, _, _, cv, _, _ in raw if math.isfinite(cv)]
    scale = max(min(finite_cv), _EPS) if finite_cv else 1.0
    rows: list[TheoryCandidate] = []
    for name, representation, validated, cv, mdl, complexity in raw:
        normalized_error = cv / scale
        score = normalized_error + description_penalty * complexity
        rows.append(
            TheoryCandidate(
                name=name,
                representation=representation,
                validated=validated,
                cv_rmse=cv,
                mdl_proxy=mdl,
                description_cost=complexity,
                score=score,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.score, row.cv_rmse, row.name)))


def _theory_prediction(theory: TheoryCandidate, point: Mapping[str, float]) -> float:
    if theory.representation is None:
        projected = point
    else:
        projected = {theory.representation.label: theory.representation.evaluate(point)}
    return float(theory.validated.predict(projected))


def rank_falsification_candidates(
    theories: Sequence[TheoryCandidate],
    points: Sequence[Mapping[str, float]],
    *,
    extrapolation_weight: float = 0.25,
) -> tuple[FalsificationCandidate, ...]:
    """Rank measurements where currently surviving theories disagree most."""

    if len(theories) < 2:
        raise ValueError("falsification ranking requires at least two theories")
    rows: list[FalsificationCandidate] = []
    for point in points:
        predictions: list[float] = []
        extrapolation_count = 0
        for theory in theories:
            try:
                predictions.append(_theory_prediction(theory, point))
                model_point = (
                    point
                    if theory.representation is None
                    else {theory.representation.label: theory.representation.evaluate(point)}
                )
                if not theory.validated.model.in_domain(model_point):
                    extrapolation_count += 1
            except (ValueError, KeyError, OverflowError, ZeroDivisionError):
                extrapolation_count += 1
        if len(predictions) < 2:
            continue
        disagreement = max(predictions) - min(predictions)
        center = sum(abs(value) for value in predictions) / len(predictions)
        relative = disagreement / max(center, _EPS)
        score = relative + extrapolation_weight * extrapolation_count / len(theories)
        rows.append(
            FalsificationCandidate(
                point=dict(point),
                disagreement=disagreement,
                relative_disagreement=relative,
                extrapolation_count=extrapolation_count,
                score=score,
            )
        )
    return tuple(sorted(rows, key=lambda row: -row.score))
