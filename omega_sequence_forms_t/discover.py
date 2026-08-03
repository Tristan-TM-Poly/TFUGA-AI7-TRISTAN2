"""Discovery orchestration for Ω-SUITE-FORM-T∞ R0.1."""
from __future__ import annotations

from fractions import Fraction
from typing import Iterable

from .exact import NumberLike, normalize_terms, vector_complexity
from .finite import (
    detect_newton_polynomial,
    difference_table,
    evaluate_newton,
    newton_expression,
    polynomial_complexity,
)
from .models import CandidateKind, DiscoveryReport, FormCandidate, OAKLevel, ValidationSummary
from .recurrence import (
    detect_linear_recurrence,
    rational_generating_coefficients,
    rational_generating_expression,
    recurrence_complexity,
    recurrence_expression,
    recurrence_value,
)


FINITE_PREFIX_WARNING = (
    "A finite prefix never identifies a unique infinite sequence without extra assumptions; "
    "reported formulas are candidates, not global theorems."
)


def discover_forms(
    values: Iterable[NumberLike],
    *,
    holdout: int | None = None,
    max_degree: int = 12,
    max_order: int = 12,
) -> DiscoveryReport:
    """Discover exact low-complexity representations for a finite prefix.

    R0.1 searches Newton polynomials and constant-coefficient linear
    recurrences, then compiles every recurrence into a rational ordinary
    generating function.  All fitting and validation use ``Fraction``.
    """

    terms = normalize_terms(values)
    held_out = _resolve_holdout(len(terms), holdout)
    training_count = len(terms) - held_out
    training = terms[:training_count]
    candidates: list[FormCandidate] = []

    polynomial = detect_newton_polynomial(training, max_degree=max_degree)
    if polynomial is not None:
        coefficients, degree = polynomial
        evaluator = lambda n, coefficients=tuple(coefficients): evaluate_newton(coefficients, n)
        validation = _validate(evaluator, terms, training_count)
        candidates.append(FormCandidate(
            kind=CandidateKind.NEWTON_POLYNOMIAL,
            expression=newton_expression(coefficients),
            parameters={
                "degree": degree,
                "newton_coefficients": coefficients,
                "basis": "binomial(n,k)",
            },
            validation=validation,
            oak_level=_oak_level(validation),
            complexity=polynomial_complexity(coefficients),
            warnings=[FINITE_PREFIX_WARNING],
            _evaluator=evaluator,
        ))

    recurrence = detect_linear_recurrence(training, max_order=max_order)
    if recurrence is not None:
        order = len(recurrence)
        seed = tuple(training[:order])
        evaluator = lambda n, seed=seed, recurrence=tuple(recurrence): recurrence_value(seed, recurrence, n)
        validation = _validate(evaluator, terms, training_count)
        level = _oak_level(validation)
        candidates.append(FormCandidate(
            kind=CandidateKind.LINEAR_RECURRENCE,
            expression=recurrence_expression(recurrence),
            parameters={
                "order": order,
                "coefficients": recurrence,
                "initial_values": seed,
            },
            validation=validation,
            oak_level=level,
            complexity=recurrence_complexity(recurrence) + vector_complexity(seed),
            warnings=[FINITE_PREFIX_WARNING],
            _evaluator=evaluator,
        ))

        numerator, denominator = rational_generating_coefficients(seed, recurrence)
        candidates.append(FormCandidate(
            kind=CandidateKind.RATIONAL_GENERATING_FUNCTION,
            expression=rational_generating_expression(numerator, denominator),
            parameters={
                "numerator_coefficients_ascending": numerator,
                "denominator_coefficients_ascending": denominator,
                "recurrence_order": order,
            },
            validation=validation,
            oak_level=level,
            complexity=(
                recurrence_complexity(recurrence)
                + vector_complexity(numerator)
                + vector_complexity(denominator)
            ),
            warnings=[
                FINITE_PREFIX_WARNING,
                "The generating function is exact conditional on the inferred recurrence.",
            ],
            _evaluator=evaluator,
        ))

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    diagnostics = _diagnostics(terms, training_count)
    diagnostics["candidate_count"] = len(candidates)
    diagnostics["search_limits"] = {"max_degree": max_degree, "max_order": max_order}

    warnings = [FINITE_PREFIX_WARNING]
    if not candidates:
        warnings.append(
            "No non-trivial polynomial or uniquely determined constant-coefficient recurrence "
            "was found inside the configured search limits."
        )
    if held_out == 0:
        warnings.append("No held-out terms were available; evidence cannot exceed OBSERVED_FIT.")

    return DiscoveryReport(
        terms=terms,
        training_terms=training_count,
        held_out_terms=held_out,
        candidates=candidates,
        diagnostics=diagnostics,
        warnings=warnings,
    )


def _resolve_holdout(length: int, requested: int | None) -> int:
    if requested is not None:
        if requested < 0:
            raise ValueError("holdout must be non-negative")
        if requested >= length:
            raise ValueError("holdout must leave at least one training term")
        return requested
    if length >= 10:
        return 3
    if length >= 7:
        return 2
    if length >= 5:
        return 1
    return 0


def _validate(evaluator, terms: tuple[Fraction, ...], training_count: int) -> ValidationSummary:
    fitted_matches = sum(evaluator(index) == terms[index] for index in range(training_count))
    held_out_matches = sum(
        evaluator(index) == terms[index] for index in range(training_count, len(terms))
    )
    return ValidationSummary(
        fitted_terms=training_count,
        fitted_matches=fitted_matches,
        held_out_terms=len(terms) - training_count,
        held_out_matches=held_out_matches,
    )


def _oak_level(validation: ValidationSummary) -> OAKLevel:
    if validation.fits_observed and validation.predicts_held_out:
        return OAKLevel.HELD_OUT_PREDICTION
    if validation.fits_observed:
        return OAKLevel.OBSERVED_FIT
    return OAKLevel.VISUAL_PATTERN


def _diagnostics(terms: tuple[Fraction, ...], training_count: int) -> dict[str, object]:
    rows = difference_table(terms)
    ratios: list[Fraction | None] = []
    for left, right in zip(terms, terms[1:]):
        ratios.append(None if left == 0 else right / left)
    return {
        "training_prefix": training_count,
        "difference_heads": [row[: min(6, len(row))] for row in rows[: min(6, len(rows))]],
        "successive_ratios": ratios[:12],
        "all_integral": all(value.denominator == 1 for value in terms),
        "contains_zero": any(value == 0 for value in terms),
    }
