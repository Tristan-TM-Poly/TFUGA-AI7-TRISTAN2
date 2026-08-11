"""Spectral geometry, companion cross-checks and inverse root design for Ω-ROOTFLOW-T∞.

This module treats a polynomial spectrum as a coupled object rather than a list
of independent roots.  It adds four OAK-safe layers on top of the exact
simple-root Jacobian:

* Frobenius companion-matrix cross-checks;
* root-separation / discriminant geometry;
* first-order covariance propagation from coefficients to roots;
* differential and iterative inverse design of coefficients for target roots.

None of these routines changes the mathematical boundary of the core: the
analytic Jacobian is valid for simple roots, while global root solving,
matching and nonlinear inverse design remain numerical procedures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import numpy.typing as npt

from .continuation import match_roots
from .core import _coefficients, polynomial_value, root_jacobian, roots

ComplexArray = npt.NDArray[np.complex128]


def companion_matrix(coefficients: npt.ArrayLike) -> ComplexArray:
    """Return the Frobenius companion matrix for ascending coefficients.

    For ``P(z)=a0+...+an*z**n``, the matrix is normalized by ``an`` and its
    eigenvalues are the finite roots of P.
    """
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    monic = coeffs[:-1] / coeffs[-1]
    matrix = np.zeros((degree, degree), dtype=np.complex128)
    if degree > 1:
        matrix[1:, :-1] = np.eye(degree - 1, dtype=np.complex128)
    matrix[:, -1] = -monic
    return matrix


@dataclass(frozen=True)
class CompanionCrosscheck:
    direct_roots: ComplexArray
    companion_roots: ComplexArray
    max_absolute_error: float
    relative_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "direct_roots": [[float(z.real), float(z.imag)] for z in self.direct_roots],
            "companion_roots": [[float(z.real), float(z.imag)] for z in self.companion_roots],
            "max_absolute_error": self.max_absolute_error,
            "relative_error": self.relative_error,
        }


def companion_crosscheck(coefficients: npt.ArrayLike) -> CompanionCrosscheck:
    """Compare polynomial roots against companion-matrix eigenvalues."""
    coeffs = _coefficients(coefficients)
    direct = roots(coeffs)
    eigenvalues = np.asarray(np.linalg.eigvals(companion_matrix(coeffs)), dtype=np.complex128)
    companion = match_roots(direct, eigenvalues)
    delta = direct - companion
    return CompanionCrosscheck(
        direct_roots=direct,
        companion_roots=companion,
        max_absolute_error=float(np.max(np.abs(delta))),
        relative_error=float(
            np.linalg.norm(delta) / max(np.linalg.norm(direct), np.finfo(float).eps)
        ),
    )


@dataclass(frozen=True)
class SpectralGeometry:
    root_count: int
    minimum_root_separation: float
    log_abs_discriminant: float
    companion_max_absolute_error: float
    companion_relative_error: float
    near_collision: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.status == "OAK_PASS_SPECTRAL_CROSSCHECK"

    def to_dict(self) -> dict[str, object]:
        return {
            "root_count": self.root_count,
            "minimum_root_separation": self.minimum_root_separation,
            "log_abs_discriminant": self.log_abs_discriminant,
            "companion_max_absolute_error": self.companion_max_absolute_error,
            "companion_relative_error": self.companion_relative_error,
            "near_collision": self.near_collision,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def root_separations(root_values: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Return all pairwise root separations |r_i-r_j|, i<j."""
    rr = np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")
    values = [abs(rr[i] - rr[j]) for i in range(rr.size) for j in range(i + 1, rr.size)]
    return np.asarray(values, dtype=float)


def log_abs_discriminant(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
) -> float:
    """Return log|Disc(P)| using roots, with -inf for a repeated root.

    ``Disc(P)=a_n**(2n-2) prod_{i<j}(r_i-r_j)**2``.
    Computing the logarithmic magnitude avoids overflow/underflow for many
    moderate-to-large spectra.
    """
    coeffs = _coefficients(coefficients)
    degree = coeffs.size - 1
    if degree <= 1:
        return 0.0
    rr = roots(coeffs) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    if rr.shape != (degree,):
        raise ValueError("root_values must contain exactly degree roots")
    separations = root_separations(rr)
    if np.any(separations == 0.0):
        return float("-inf")
    return float((2 * degree - 2) * np.log(abs(coeffs[-1])) + 2.0 * np.sum(np.log(separations)))


def audit_spectral_geometry(
    coefficients: npt.ArrayLike,
    *,
    collision_tolerance: float = 1e-7,
    companion_relative_tolerance: float = 1e-10,
) -> SpectralGeometry:
    """OAK-style independent spectral geometry audit."""
    if collision_tolerance <= 0 or companion_relative_tolerance <= 0:
        raise ValueError("tolerances must be positive")
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs)
    separations = root_separations(rr)
    minimum = float(np.min(separations)) if separations.size else float("inf")
    crosscheck = companion_crosscheck(coeffs)
    near = bool(minimum <= collision_tolerance)
    if near:
        status = "OAK_WARN_ROOT_COLLISION"
    elif crosscheck.relative_error > companion_relative_tolerance:
        status = "OAK_WARN_COMPANION_MISMATCH"
    else:
        status = "OAK_PASS_SPECTRAL_CROSSCHECK"
    return SpectralGeometry(
        root_count=int(rr.size),
        minimum_root_separation=minimum,
        log_abs_discriminant=log_abs_discriminant(coeffs, rr),
        companion_max_absolute_error=crosscheck.max_absolute_error,
        companion_relative_error=crosscheck.relative_error,
        near_collision=near,
        status=status,
    )


def propagate_root_covariance(
    coefficients: npt.ArrayLike,
    coefficient_covariance: npt.ArrayLike,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> ComplexArray:
    """First-order covariance propagation ``Sigma_r = J Sigma_a J^H``.

    The result is a Hermitian covariance of complex root displacements.  It is
    a local linearization, not a guarantee that a broad coefficient posterior
    remains Gaussian after passing near a discriminant.
    """
    coeffs = _coefficients(coefficients)
    covariance = np.asarray(coefficient_covariance, dtype=np.complex128)
    if covariance.shape != (coeffs.size, coeffs.size):
        raise ValueError("coefficient_covariance must be square with coefficient dimension")
    if not np.allclose(covariance, covariance.conj().T, atol=1e-12, rtol=0.0):
        raise ValueError("coefficient_covariance must be Hermitian")
    eigenvalues = np.linalg.eigvalsh(covariance)
    if np.min(eigenvalues) < -1e-12:
        raise ValueError("coefficient_covariance must be positive semidefinite")
    jac = root_jacobian(
        coeffs,
        root_values,
        singularity_tolerance=singularity_tolerance,
    )
    result = jac @ covariance @ jac.conj().T
    return 0.5 * (result + result.conj().T)


@dataclass(frozen=True)
class LinearizedInverseDesign:
    coefficient_update: ComplexArray
    predicted_root_update: ComplexArray
    residual: ComplexArray
    residual_norm: float
    rank: int
    condition_number: float
    free_indices: tuple[int, ...]
    real_coefficients: bool


def _free_index_tuple(count: int, free_indices: Iterable[int] | None) -> tuple[int, ...]:
    if free_indices is None:
        # Fix the leading coefficient by default.  This removes the projective
        # scaling null direction while retaining every physical root degree of
        # freedom for a monic representation.
        return tuple(range(count - 1))
    indices = tuple(int(index) for index in free_indices)
    if not indices:
        raise ValueError("free_indices must not be empty")
    if len(set(indices)) != len(indices):
        raise ValueError("free_indices must be unique")
    if min(indices) < 0 or max(indices) >= count:
        raise ValueError("free_indices contain an out-of-range coefficient")
    return indices


def linearized_inverse_design(
    coefficients: npt.ArrayLike,
    root_values: npt.ArrayLike,
    desired_root_update: npt.ArrayLike,
    *,
    free_indices: Iterable[int] | None = None,
    real_coefficients: bool = True,
    singularity_tolerance: float = 1e-12,
) -> LinearizedInverseDesign:
    """Solve ``J da ~= dr*`` by least squares in a gauge-fixed subspace."""
    coeffs = _coefficients(coefficients)
    rr = np.asarray(root_values, dtype=np.complex128)
    desired = np.asarray(desired_root_update, dtype=np.complex128)
    if rr.ndim != 1 or desired.shape != rr.shape:
        raise ValueError("root_values and desired_root_update must be matching vectors")
    indices = _free_index_tuple(coeffs.size, free_indices)
    jac = root_jacobian(
        coeffs,
        rr,
        singularity_tolerance=singularity_tolerance,
    )
    reduced = jac[:, indices]
    if real_coefficients:
        matrix = np.vstack([reduced.real, reduced.imag])
        target = np.concatenate([desired.real, desired.imag])
        solved, _, rank, singular_values = np.linalg.lstsq(matrix, target, rcond=None)
        reduced_update = solved.astype(np.complex128)
    else:
        reduced_update, _, rank, singular_values = np.linalg.lstsq(reduced, desired, rcond=None)
    update = np.zeros(coeffs.size, dtype=np.complex128)
    update[np.asarray(indices, dtype=int)] = reduced_update
    predicted = jac @ update
    residual = desired - predicted
    if singular_values.size == 0 or np.min(singular_values) <= np.finfo(float).eps:
        condition = float("inf")
    else:
        condition = float(np.max(singular_values) / np.min(singular_values))
    return LinearizedInverseDesign(
        coefficient_update=update,
        predicted_root_update=predicted,
        residual=residual,
        residual_norm=float(np.linalg.norm(residual)),
        rank=int(rank),
        condition_number=condition,
        free_indices=indices,
        real_coefficients=bool(real_coefficients),
    )


@dataclass(frozen=True)
class InverseDesignStep:
    iteration: int
    root_error_norm: float
    update_norm: float
    accepted_scale: float
    linear_rank: int
    linear_condition_number: float
    max_root_residual: float


@dataclass(frozen=True)
class InverseDesignResult:
    coefficients: ComplexArray
    roots: ComplexArray
    target_roots: ComplexArray
    steps: tuple[InverseDesignStep, ...]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def root_error_norm(self) -> float:
        return float(np.linalg.norm(self.target_roots - self.roots))

    @property
    def converged(self) -> bool:
        return self.status == "OAK_CONVERGED_INVERSE_DESIGN"


def inverse_design_roots(
    initial_coefficients: npt.ArrayLike,
    target_roots: npt.ArrayLike,
    *,
    free_indices: Iterable[int] | None = None,
    real_coefficients: bool = True,
    max_iterations: int = 24,
    tolerance: float = 1e-10,
    max_relative_step: float = 0.5,
    singularity_tolerance: float = 1e-10,
) -> InverseDesignResult:
    """Iteratively move polynomial coefficients toward a target root spectrum.

    Each iteration solves the local differential inverse problem, limits the
    coefficient update by a trust radius, then performs a monotone backtracking
    line search against the actual nonlinear roots.  The leading coefficient is
    fixed by default to remove projective gauge freedom.
    """
    coeffs = _coefficients(initial_coefficients).copy()
    target = np.asarray(target_roots, dtype=np.complex128)
    degree = coeffs.size - 1
    if target.shape != (degree,):
        raise ValueError("target_roots must contain exactly degree roots")
    if max_iterations <= 0 or tolerance <= 0 or max_relative_step <= 0:
        raise ValueError("max_iterations, tolerance and max_relative_step must be positive")
    if real_coefficients and np.max(np.abs(coeffs.imag)) > 1e-12:
        raise ValueError("real_coefficients=True requires real initial coefficients")

    current = roots(coeffs)
    target = match_roots(current, target)
    records: list[InverseDesignStep] = []
    status = "OAK_WARN_MAX_ITERATIONS"

    for iteration in range(max_iterations + 1):
        error = target - current
        error_norm = float(np.linalg.norm(error))
        if error_norm <= tolerance:
            status = "OAK_CONVERGED_INVERSE_DESIGN"
            break
        if iteration == max_iterations:
            break

        linear = linearized_inverse_design(
            coeffs,
            current,
            error,
            free_indices=free_indices,
            real_coefficients=real_coefficients,
            singularity_tolerance=singularity_tolerance,
        )
        update = linear.coefficient_update.copy()
        update_norm = float(np.linalg.norm(update))
        trust_radius = max_relative_step * max(float(np.linalg.norm(coeffs)), 1.0)
        if update_norm > trust_radius:
            update *= trust_radius / update_norm
            update_norm = trust_radius

        accepted = False
        accepted_scale = 0.0
        trial_roots = current
        trial_coeffs = coeffs
        for exponent in range(14):
            scale = 0.5**exponent
            candidate_coeffs = coeffs + scale * update
            if real_coefficients:
                candidate_coeffs = candidate_coeffs.real.astype(np.complex128)
            if abs(candidate_coeffs[-1]) <= np.finfo(float).eps:
                continue
            candidate_roots = match_roots(current, roots(candidate_coeffs))
            candidate_error = float(np.linalg.norm(target - candidate_roots))
            if candidate_error < error_norm:
                accepted = True
                accepted_scale = scale
                trial_coeffs = candidate_coeffs
                trial_roots = candidate_roots
                break

        if not accepted:
            status = "OAK_WARN_INVERSE_DESIGN_STALLED"
            records.append(
                InverseDesignStep(
                    iteration=iteration,
                    root_error_norm=error_norm,
                    update_norm=update_norm,
                    accepted_scale=0.0,
                    linear_rank=linear.rank,
                    linear_condition_number=linear.condition_number,
                    max_root_residual=float(max(abs(polynomial_value(coeffs, r)) for r in current)),
                )
            )
            break

        coeffs = trial_coeffs
        current = trial_roots
        records.append(
            InverseDesignStep(
                iteration=iteration,
                root_error_norm=error_norm,
                update_norm=update_norm,
                accepted_scale=accepted_scale,
                linear_rank=linear.rank,
                linear_condition_number=linear.condition_number,
                max_root_residual=float(max(abs(polynomial_value(coeffs, r)) for r in current)),
            )
        )

    return InverseDesignResult(
        coefficients=coeffs,
        roots=current,
        target_roots=target,
        steps=tuple(records),
        status=status,
    )
