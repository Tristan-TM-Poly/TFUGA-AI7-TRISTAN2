from __future__ import annotations

"""Streaming operator grammar with constraint pruning.

The generator has no permanent total-item ceiling. A caller may impose a real
resource budget for a finite run; the grammar itself remains lazy.
"""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations_with_replacement
import time
from typing import Callable, Iterable, Iterator, Sequence

from .lagrangian_ir import operator_mass_dimension, operator_u1_charge
from .types import EpistemicStatus, FieldKind, FieldSpec, OperatorFactor, OperatorSpec, TheorySpec


@dataclass(frozen=True, slots=True)
class OperatorGenerationBudget:
    max_seconds: float | None = None
    max_bytes_estimate: int | None = None
    quality_floor: float = 0.0
    stop_requested: Callable[[], bool] | None = None


@dataclass(frozen=True, slots=True)
class GeneratedOperator:
    operator: OperatorSpec
    score: float
    fingerprint: str
    reasons: tuple[str, ...]


def _spin_parity(fields: Sequence[FieldSpec]) -> int:
    fermions = sum(1 for field in fields if field.kind is FieldKind.FERMION)
    return fermions % 2


def _estimated_bytes(operator: OperatorSpec) -> int:
    return 120 + sum(60 + len(factor.field_id) for factor in operator.factors)


def operator_fertility_score(operator: OperatorSpec, theory: TheorySpec) -> tuple[float, tuple[str, ...]]:
    dimension = operator_mass_dimension(operator, theory)
    reasons: list[str] = []
    score = 1.0
    if dimension <= 4:
        score += 2.0
        reasons.append("renormalizable_or_relevant")
    elif dimension <= 6:
        score += 1.0
        reasons.append("leading_eft")
    else:
        score -= float(dimension - 6) * 0.25
        reasons.append("high_dimension_penalty")
    if operator.hermitian:
        score += 0.5
        reasons.append("hermiticity_declared")
    if operator.lorentz_scalar:
        score += 0.5
        reasons.append("lorentz_scalar_declared")
    if all(operator_u1_charge(operator, theory, group) == 0 for group in theory.gauge_groups if group.startswith("U1")):
        score += 1.0
        reasons.append("u1_invariant")
    unique_fields = len({factor.field_id for factor in operator.factors})
    score += min(unique_fields, 4) * 0.1
    return score, tuple(reasons)


def _candidate_operator(field_ids: tuple[str, ...], theory: TheorySpec) -> OperatorSpec:
    counts: dict[str, int] = {}
    for field_id in field_ids:
        counts[field_id] = counts.get(field_id, 0) + 1
    factors = tuple(
        OperatorFactor(field_id=field_id, multiplicity=multiplicity)
        for field_id, multiplicity in sorted(counts.items())
    )
    token = "__".join(f"{field_id}_{multiplicity}" for field_id, multiplicity in sorted(counts.items()))
    digest = sha256(token.encode("utf-8")).hexdigest()[:16]
    return OperatorSpec(
        id=f"generated.operator.{digest}",
        coefficient=f"c_{digest}",
        factors=factors,
        hermitian=None,
        lorentz_scalar=True,
        status=EpistemicStatus.EXPLORATORY,
        tags=("generated", "requires_review"),
        metadata={"generator": "omega_pct_t.r03max.operators"},
    )


def generate_scalar_monomials(
    theory: TheorySpec,
    *,
    maximum_mass_dimension: Fraction = Fraction(6),
    minimum_arity: int = 2,
    maximum_arity: int | None = None,
    budget: OperatorGenerationBudget | None = None,
) -> Iterator[GeneratedOperator]:
    """Yield gauge-filtered scalar monomials lazily.

    ``maximum_arity`` is a grammar choice for one campaign, not a permanent
    system ceiling. If omitted, it is derived from the smallest positive field
    mass dimension and the requested operator dimension.
    """

    if maximum_mass_dimension <= 0:
        return
    fields = tuple(field for field in theory.fields if field.kind is not FieldKind.GHOST)
    positive_dimensions = [field.mass_dimension for field in fields if field.mass_dimension > 0]
    if not positive_dimensions:
        return
    if maximum_arity is None:
        maximum_arity = int(maximum_mass_dimension / min(positive_dimensions))
    start = time.monotonic()
    bytes_estimate = 0
    seen: set[str] = set()
    effective_budget = budget or OperatorGenerationBudget()
    field_map = theory.field_map()
    for arity in range(minimum_arity, maximum_arity + 1):
        for selection in combinations_with_replacement(tuple(field_map), arity):
            if effective_budget.stop_requested and effective_budget.stop_requested():
                return
            if effective_budget.max_seconds is not None and time.monotonic() - start >= effective_budget.max_seconds:
                return
            selected_fields = tuple(field_map[field_id] for field_id in selection)
            if _spin_parity(selected_fields) != 0:
                continue
            operator = _candidate_operator(selection, theory)
            dimension = operator_mass_dimension(operator, theory)
            if dimension > maximum_mass_dimension:
                continue
            if any(
                operator_u1_charge(operator, theory, group) != 0
                for group in theory.gauge_groups
                if group.startswith("U1")
            ):
                continue
            fingerprint = sha256(repr(operator).encode("utf-8")).hexdigest()
            if fingerprint in seen:
                continue
            score, reasons = operator_fertility_score(operator, theory)
            if score < effective_budget.quality_floor:
                continue
            item_bytes = _estimated_bytes(operator)
            if (
                effective_budget.max_bytes_estimate is not None
                and bytes_estimate + item_bytes > effective_budget.max_bytes_estimate
            ):
                return
            bytes_estimate += item_bytes
            seen.add(fingerprint)
            yield GeneratedOperator(operator, score, fingerprint, reasons)


def take(iterable: Iterable[GeneratedOperator], count: int) -> tuple[GeneratedOperator, ...]:
    if count < 0:
        raise ValueError("count must be non-negative")
    result: list[GeneratedOperator] = []
    for item in iterable:
        if len(result) >= count:
            break
        result.append(item)
    return tuple(result)
