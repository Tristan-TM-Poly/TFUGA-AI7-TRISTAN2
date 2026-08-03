"""Exact quasi-polynomial discovery by residue-class Newton expansions."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb
from typing import Iterable, Sequence

from ..exact import NumberLike, normalize_terms
from ..finite import detect_newton_polynomial, evaluate_newton


@dataclass(frozen=True)
class QuasiPolynomialBranch:
    residue: int
    period: int
    coefficients: tuple[Fraction, ...]
    sample_count: int

    @property
    def degree(self) -> int:
        return len(self.coefficients) - 1

    def evaluate(self, n: int) -> Fraction:
        if n < 0:
            raise ValueError("n must be non-negative")
        if n % self.period != self.residue:
            raise ValueError("index does not belong to this branch")
        local_index = (n - self.residue) // self.period
        return evaluate_newton(self.coefficients, local_index)

    def expression(self) -> str:
        terms = []
        for k, coefficient in enumerate(self.coefficients):
            if coefficient:
                terms.append(f"({coefficient})*C((n-{self.residue})/{self.period},{k})")
        return " + ".join(terms) if terms else "0"


@dataclass(frozen=True)
class QuasiPolynomialCandidate:
    period: int
    branches: tuple[QuasiPolynomialBranch, ...]
    fitted_terms: int
    fitted_matches: int
    held_out_terms: int
    held_out_matches: int
    training_terms: int
    total_terms: int

    @property
    def maximum_degree(self) -> int:
        return max(branch.degree for branch in self.branches)

    @property
    def exact_fit(self) -> bool:
        return self.fitted_terms == self.fitted_matches

    @property
    def predicts_holdout(self) -> bool:
        return self.held_out_terms > 0 and self.held_out_terms == self.held_out_matches

    @property
    def complexity(self) -> int:
        return self.period + sum(len(branch.coefficients) for branch in self.branches)

    def evaluate(self, n: int) -> Fraction:
        return self.branches[n % self.period].evaluate(n)

    def expression(self) -> str:
        return " ; ".join(
            f"n≡{branch.residue} (mod {self.period}): {branch.expression()}"
            for branch in self.branches
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "family": "quasi_polynomial",
            "period": self.period,
            "maximum_degree": self.maximum_degree,
            "branches": [
                {
                    "residue": branch.residue,
                    "degree": branch.degree,
                    "coefficients": [str(value) for value in branch.coefficients],
                    "sample_count": branch.sample_count,
                    "expression": branch.expression(),
                }
                for branch in self.branches
            ],
            "expression": self.expression(),
            "validation": {
                "fitted_terms": self.fitted_terms,
                "fitted_matches": self.fitted_matches,
                "held_out_terms": self.held_out_terms,
                "held_out_matches": self.held_out_matches,
            },
            "complexity": self.complexity,
            "global_identity_proved": False,
        }


def _default_holdout(term_count: int) -> int:
    if term_count < 8:
        return 0
    return max(2, min(term_count // 4, 16))


def _fit_branch(values: Sequence[Fraction], max_degree: int) -> tuple[Fraction, ...] | None:
    if len(values) < 2:
        return None
    result = detect_newton_polynomial(values, max_degree=max_degree)
    if result is None:
        return None
    coefficients, _degree = result
    return tuple(coefficients)


def fit_quasi_polynomial(
    terms: Iterable[NumberLike],
    *,
    period: int,
    max_degree: int = 12,
    holdout: int | None = None,
) -> QuasiPolynomialCandidate | None:
    values = normalize_terms(terms)
    if period <= 0:
        raise ValueError("period must be positive")
    if max_degree < 0:
        raise ValueError("max_degree must be non-negative")
    if holdout is None:
        holdout = _default_holdout(len(values))
    if not 0 <= holdout < len(values):
        raise ValueError("holdout must lie in [0, len(terms))")
    training_count = len(values) - holdout
    if training_count < 2 * period:
        return None

    branches: list[QuasiPolynomialBranch] = []
    for residue in range(period):
        branch_values = tuple(values[index] for index in range(residue, training_count, period))
        coefficients = _fit_branch(branch_values, max_degree)
        if coefficients is None:
            return None
        branches.append(
            QuasiPolynomialBranch(
                residue=residue,
                period=period,
                coefficients=coefficients,
                sample_count=len(branch_values),
            )
        )

    candidate = QuasiPolynomialCandidate(
        period=period,
        branches=tuple(branches),
        fitted_terms=training_count,
        fitted_matches=sum(candidate_value == values[index] for index, candidate_value in (
            (index, branches[index % period].evaluate(index)) for index in range(training_count)
        )),
        held_out_terms=holdout,
        held_out_matches=sum(
            branches[index % period].evaluate(index) == values[index]
            for index in range(training_count, len(values))
        ),
        training_terms=training_count,
        total_terms=len(values),
    )
    if not candidate.exact_fit:
        return None
    return candidate


def discover_quasi_polynomials(
    terms: Iterable[NumberLike],
    *,
    max_period: int = 32,
    max_degree: int = 12,
    holdout: int | None = None,
    require_nontrivial_period: bool = True,
) -> tuple[QuasiPolynomialCandidate, ...]:
    values = normalize_terms(terms)
    if max_period <= 0:
        raise ValueError("max_period must be positive")
    candidates = []
    first_period = 2 if require_nontrivial_period else 1
    upper = min(max_period, max(1, len(values) // 2))
    for period in range(first_period, upper + 1):
        candidate = fit_quasi_polynomial(
            values,
            period=period,
            max_degree=max_degree,
            holdout=holdout,
        )
        if candidate is not None:
            candidates.append(candidate)
    candidates.sort(
        key=lambda item: (
            not item.predicts_holdout,
            item.complexity,
            item.period,
            item.maximum_degree,
        )
    )
    return tuple(candidates)


def quasi_polynomial_fixture(period: int, degree: int, count: int) -> tuple[Fraction, ...]:
    """Deterministic benchmark fixture with branch-distinct integer values."""

    if period <= 0 or degree < 0 or count <= 0:
        raise ValueError("invalid fixture dimensions")
    values = []
    for n in range(count):
        residue = n % period
        local = (n - residue) // period
        value = Fraction((residue + 1) * (local + 1) ** degree + residue * residue)
        values.append(value)
    return tuple(values)
