"""Branch tracking and monodromy of polynomial roots for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np
import numpy.typing as npt

from .continuation import match_roots, newton_refine
from .core import _coefficients, derivative_value, polynomial_value, root_jacobian, roots

ComplexArray = npt.NDArray[np.complex128]


def _assignment(reference: ComplexArray, candidates: ComplexArray) -> tuple[int, ...]:
    """Return candidate indices minimizing total distance from reference entries."""
    if reference.shape != candidates.shape:
        raise ValueError("reference and candidates must have matching shape")
    count = reference.size
    if count <= 8:
        best: tuple[int, ...] | None = None
        best_cost = float("inf")
        for perm in permutations(range(count)):
            cost = float(sum(abs(reference[i] - candidates[perm[i]]) for i in range(count)))
            if cost < best_cost:
                best_cost = cost
                best = tuple(int(index) for index in perm)
        assert best is not None
        return best
    remaining = list(range(count))
    result: list[int] = []
    for value in reference:
        index = min(remaining, key=lambda j: (abs(value - candidates[j]), j))
        result.append(index)
        remaining.remove(index)
    return tuple(result)


@dataclass(frozen=True)
class PathTrackingStep:
    path_segment: int
    local_fraction: float
    coefficients: ComplexArray
    roots: ComplexArray
    predictor_residual: float
    corrected_residual: float
    minimum_derivative: float


@dataclass(frozen=True)
class MonodromyResult:
    initial_roots: ComplexArray
    final_roots: ComplexArray
    permutation: tuple[int, ...]
    steps: tuple[PathTrackingStep, ...]
    closed_coefficient_loop: bool
    maximum_corrected_residual: float
    minimum_derivative: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def is_identity(self) -> bool:
        return self.permutation == tuple(range(len(self.permutation)))

    def to_dict(self) -> dict[str, object]:
        return {
            "initial_roots": [[float(z.real), float(z.imag)] for z in self.initial_roots],
            "final_roots": [[float(z.real), float(z.imag)] for z in self.final_roots],
            "permutation": list(self.permutation),
            "closed_coefficient_loop": self.closed_coefficient_loop,
            "maximum_corrected_residual": self.maximum_corrected_residual,
            "minimum_derivative": self.minimum_derivative,
            "identity_monodromy": self.is_identity,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def track_coefficient_path(
    coefficient_path: npt.ArrayLike,
    *,
    subdivisions: int = 4,
    singularity_tolerance: float = 1e-9,
    newton_tolerance: float = 1e-12,
    closed_tolerance: float = 1e-10,
) -> MonodromyResult:
    """Track ordered root branches along a piecewise-linear coefficient path.

    Unlike repeatedly calling a fresh polynomial solver, the ordering is carried
    from step to step by the analytic differential predictor.  Direct roots at
    each corrected coefficient vector are used only as an independent OAK set
    against which the corrected branch guesses are matched.
    """
    path = np.asarray(coefficient_path, dtype=np.complex128)
    if path.ndim != 2 or path.shape[0] < 2 or path.shape[1] < 2:
        raise ValueError("coefficient_path must be a 2D array with at least two points")
    if subdivisions <= 0:
        raise ValueError("subdivisions must be positive")
    if singularity_tolerance <= 0 or newton_tolerance <= 0 or closed_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    for row in path:
        _coefficients(row)

    current = roots(path[0])
    initial = current.copy()
    records: list[PathTrackingStep] = []
    maximum_residual = float(max(abs(polynomial_value(path[0], r)) for r in current))
    minimum_derivative = float(min(abs(derivative_value(path[0], r)) for r in current))
    if minimum_derivative <= singularity_tolerance:
        raise np.linalg.LinAlgError("coefficient path starts too near the discriminant")

    for segment in range(path.shape[0] - 1):
        segment_start = path[segment]
        segment_end = path[segment + 1]
        segment_delta = segment_end - segment_start
        for local_index in range(1, subdivisions + 1):
            f0 = (local_index - 1) / subdivisions
            f1 = local_index / subdivisions
            coeff0 = segment_start + f0 * segment_delta
            coeff1 = segment_start + f1 * segment_delta
            delta = coeff1 - coeff0
            jac = root_jacobian(
                coeff0,
                current,
                singularity_tolerance=singularity_tolerance,
            )
            predicted = current + jac @ delta
            predictor_residual = float(
                max(abs(polynomial_value(coeff1, root)) for root in predicted)
            )
            corrected_guess = np.empty_like(predicted)
            for index, guess in enumerate(predicted):
                corrected_guess[index], _, _ = newton_refine(
                    coeff1,
                    complex(guess),
                    tolerance=newton_tolerance,
                    singularity_tolerance=min(singularity_tolerance, 1e-12),
                )
            corrected = match_roots(corrected_guess, roots(coeff1))
            corrected_residual = float(
                max(abs(polynomial_value(coeff1, root)) for root in corrected)
            )
            current_minimum = float(
                min(abs(derivative_value(coeff1, root)) for root in corrected)
            )
            if current_minimum <= singularity_tolerance:
                raise np.linalg.LinAlgError(
                    f"coefficient path approaches unresolved discriminant at segment {segment}"
                )
            current = corrected
            maximum_residual = max(maximum_residual, corrected_residual)
            minimum_derivative = min(minimum_derivative, current_minimum)
            records.append(
                PathTrackingStep(
                    path_segment=segment,
                    local_fraction=float(f1),
                    coefficients=coeff1.copy(),
                    roots=current.copy(),
                    predictor_residual=predictor_residual,
                    corrected_residual=corrected_residual,
                    minimum_derivative=current_minimum,
                )
            )

    closed = bool(
        np.linalg.norm(path[-1] - path[0])
        <= closed_tolerance * max(np.linalg.norm(path[0]), 1.0)
    )
    permutation = _assignment(current, initial)
    if closed:
        status = "OAK_PASS_MONODROMY_LOOP"
    else:
        status = "OAK_PASS_BRANCH_PATH"
    return MonodromyResult(
        initial_roots=initial,
        final_roots=current,
        permutation=permutation,
        steps=tuple(records),
        closed_coefficient_loop=closed,
        maximum_corrected_residual=maximum_residual,
        minimum_derivative=minimum_derivative,
        status=status,
    )


def quadratic_square_root_loop(samples: int = 17) -> ComplexArray:
    """Canonical loop P_theta(z)=z^2-exp(i theta) around the discriminant t=0."""
    if samples < 5:
        raise ValueError("samples must be >= 5")
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    return np.asarray(
        [[-np.exp(1j * value), 0.0 + 0j, 1.0 + 0j] for value in theta],
        dtype=np.complex128,
    )
