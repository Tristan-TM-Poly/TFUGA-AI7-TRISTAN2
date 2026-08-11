"""Predictor-corrector continuation and branch matching for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, polynomial_value, root_jacobian, roots

ComplexArray = npt.NDArray[np.complex128]


def match_roots(reference: npt.ArrayLike, candidates: npt.ArrayLike) -> ComplexArray:
    """Reorder candidates to minimize total distance to reference."""
    ref = np.asarray(reference, dtype=np.complex128)
    cand = np.asarray(candidates, dtype=np.complex128)
    if ref.ndim != 1 or cand.shape != ref.shape:
        raise ValueError("reference and candidates must be matching root vectors")
    n = ref.size
    if n <= 8:
        best_perm: tuple[int, ...] | None = None
        best_cost = float("inf")
        for perm in permutations(range(n)):
            cost = float(sum(abs(ref[i] - cand[perm[i]]) for i in range(n)))
            if cost < best_cost:
                best_cost = cost
                best_perm = perm
        assert best_perm is not None
        return cand[np.asarray(best_perm, dtype=int)]

    remaining = list(range(n))
    ordered = np.empty(n, dtype=np.complex128)
    for i, value in enumerate(ref):
        index = min(remaining, key=lambda j: (abs(value - cand[j]), j))
        ordered[i] = cand[index]
        remaining.remove(index)
    return ordered


def newton_refine(
    coefficients: npt.ArrayLike,
    initial: complex,
    *,
    max_iterations: int = 20,
    tolerance: float = 1e-12,
    singularity_tolerance: float = 1e-14,
) -> tuple[complex, int, float]:
    """Refine one root guess and return (root, iterations, residual)."""
    coeffs = _coefficients(coefficients)
    if max_iterations <= 0 or tolerance <= 0 or singularity_tolerance <= 0:
        raise ValueError("iterations and tolerances must be positive")
    z = complex(initial)
    for iteration in range(1, max_iterations + 1):
        value = complex(polynomial_value(coeffs, z))
        if abs(value) <= tolerance:
            return z, iteration - 1, float(abs(value))
        p1 = derivative_value(coeffs, z)
        if abs(p1) <= singularity_tolerance:
            raise np.linalg.LinAlgError("Newton correction encountered a near-critical P'(z)")
        z -= value / p1
    residual = float(abs(polynomial_value(coeffs, z)))
    return z, max_iterations, residual


@dataclass(frozen=True)
class ContinuationStep:
    parameter: float
    coefficients: ComplexArray
    roots: ComplexArray
    predictor_residual: float
    corrected_residual: float
    minimum_derivative: float


@dataclass(frozen=True)
class ContinuationResult:
    steps: tuple[ContinuationStep, ...]

    @property
    def final_roots(self) -> ComplexArray:
        return self.steps[-1].roots.copy()


def continue_roots(
    start_coefficients: npt.ArrayLike,
    end_coefficients: npt.ArrayLike,
    *,
    steps: int = 32,
    singularity_tolerance: float = 1e-10,
    newton_tolerance: float = 1e-12,
) -> ContinuationResult:
    """Track roots along a straight path in coefficient space.

    The analytic root Jacobian supplies the predictor and Newton supplies the
    corrector. Direct roots are used only for deterministic one-to-one branch
    assignment, which also makes this an OAK benchmark of the predictor.
    """
    start = _coefficients(start_coefficients)
    end = _coefficients(end_coefficients)
    if start.shape != end.shape:
        raise ValueError("start and end coefficients must have identical degree")
    if steps <= 0:
        raise ValueError("steps must be positive")

    current_roots = roots(start)
    records: list[ContinuationStep] = [
        ContinuationStep(
            parameter=0.0,
            coefficients=start.copy(),
            roots=current_roots.copy(),
            predictor_residual=0.0,
            corrected_residual=float(max(abs(polynomial_value(start, r)) for r in current_roots)),
            minimum_derivative=float(min(abs(derivative_value(start, r)) for r in current_roots)),
        )
    ]

    delta_total = end - start
    for index in range(1, steps + 1):
        t0 = (index - 1) / steps
        t1 = index / steps
        coeff0 = start + t0 * delta_total
        coeff1 = start + t1 * delta_total
        delta = coeff1 - coeff0
        jac = root_jacobian(
            coeff0, current_roots, singularity_tolerance=singularity_tolerance
        )
        predicted = current_roots + jac @ delta
        predictor_residual = float(max(abs(polynomial_value(coeff1, r)) for r in predicted))

        corrected = np.empty_like(predicted)
        for j, guess in enumerate(predicted):
            corrected[j], _, _ = newton_refine(
                coeff1,
                complex(guess),
                tolerance=newton_tolerance,
                singularity_tolerance=min(singularity_tolerance, 1e-12),
            )
        spectrum = roots(coeff1)
        corrected = match_roots(corrected, spectrum)
        corrected_residual = float(max(abs(polynomial_value(coeff1, r)) for r in corrected))
        minimum_derivative = float(min(abs(derivative_value(coeff1, r)) for r in corrected))
        current_roots = corrected
        records.append(
            ContinuationStep(
                parameter=float(t1),
                coefficients=coeff1.copy(),
                roots=current_roots.copy(),
                predictor_residual=predictor_residual,
                corrected_residual=corrected_residual,
                minimum_derivative=minimum_derivative,
            )
        )

    return ContinuationResult(tuple(records))
