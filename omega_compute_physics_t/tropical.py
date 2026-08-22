"""Tropical / Newton-polytope views of multivariate empirical complexity laws.

For a nonnegative monomial family sum c_alpha x^alpha and anisotropic scaling
x_i=lambda**v_i, each term scales as lambda**(alpha dot v). The maximum dot
product identifies the asymptotically dominant *candidate term* when
coefficients do not cancel. This is structural mathematics on a supplied model,
not proof that the fitted model is the program's true asymptotic complexity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .atlas import EmpiricalResourceModel


@dataclass(frozen=True)
class ExponentTerm:
    label: str
    coefficient: float
    exponents: tuple[float, ...]


@dataclass(frozen=True)
class DirectionalDominance:
    direction: tuple[float, ...]
    degree: float
    dominant_terms: tuple[str, ...]
    status: str = "model-conditioned-tropical-dominance"
    oak_warning: str = (
        "Dominance is computed inside the supplied empirical symbolic model. It does not "
        "prove the program's asymptotic complexity and can fail under cancellation or model drift."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def monomial_terms(model: EmpiricalResourceModel, *, coefficient_threshold: float = 1e-12) -> tuple[ExponentTerm, ...]:
    rows: list[ExponentTerm] = []
    for feature, coefficient in zip(model.features, model.coefficients):
        if feature.kind != "monomial" or abs(coefficient) <= coefficient_threshold:
            continue
        exponent_map = {name: float(power) for name, power in zip(feature.variables, feature.powers)}
        rows.append(
            ExponentTerm(
                label=feature.label,
                coefficient=float(coefficient),
                exponents=tuple(exponent_map.get(name, 0.0) for name in model.variables),
            )
        )
    return tuple(rows)


def directional_dominance(
    model: EmpiricalResourceModel,
    direction: Mapping[str, float] | Sequence[float],
    *,
    tolerance: float = 1e-12,
) -> DirectionalDominance:
    terms = monomial_terms(model)
    if not terms:
        raise ValueError("model has no active monomial terms")
    if isinstance(direction, Mapping):
        vector = tuple(float(direction[name]) for name in model.variables)
    else:
        vector = tuple(float(value) for value in direction)
        if len(vector) != len(model.variables):
            raise ValueError("direction dimension must match model variables")
    scores = [sum(a * v for a, v in zip(term.exponents, vector)) for term in terms]
    best = max(scores)
    dominant = tuple(term.label for term, score in zip(terms, scores) if abs(score - best) <= tolerance)
    return DirectionalDominance(direction=vector, degree=best, dominant_terms=dominant)


def asymptotic_direction_spectrum(
    model: EmpiricalResourceModel,
    directions: Sequence[Mapping[str, float] | Sequence[float]],
) -> tuple[DirectionalDominance, ...]:
    return tuple(directional_dominance(model, direction) for direction in directions)


def dominance_signature(model: EmpiricalResourceModel, directions: Sequence[Sequence[float]]) -> dict[str, Any]:
    rows = asymptotic_direction_spectrum(model, directions)
    return {
        "variables": list(model.variables),
        "directions": [row.to_dict() for row in rows],
        "distinct_dominant_terms": sorted({term for row in rows for term in row.dominant_terms}),
        "status": "model-conditioned-asymptotic-direction-spectrum",
        "oak_warning": (
            "This signature describes the fitted model's Newton/tropical geometry only. "
            "It is not an asymptotic proof about the underlying implementation."
        ),
    }
