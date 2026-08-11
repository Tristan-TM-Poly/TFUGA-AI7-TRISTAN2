"""OAK validation utilities for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .continuation import match_roots
from .core import _coefficients, projective_scaling_residual, root_conditions, root_jacobian, roots

ComplexArray = npt.NDArray[np.complex128]


def finite_difference_root_jacobian(
    coefficients: npt.ArrayLike,
    *,
    step: float = 1e-7,
) -> ComplexArray:
    """Central finite-difference Jacobian used only as an independent check."""
    coeffs = _coefficients(coefficients)
    if step <= 0:
        raise ValueError("step must be positive")
    base = roots(coeffs)
    result = np.empty((base.size, coeffs.size), dtype=np.complex128)
    for k in range(coeffs.size):
        plus = coeffs.copy()
        minus = coeffs.copy()
        plus[k] += step
        minus[k] -= step
        plus_roots = match_roots(base, roots(plus))
        minus_roots = match_roots(base, roots(minus))
        result[:, k] = (plus_roots - minus_roots) / (2.0 * step)
    return result


@dataclass(frozen=True)
class RootFlowAudit:
    root_count: int
    max_root_residual: float
    minimum_derivative: float
    maximum_reciprocal_derivative: float
    projective_scaling_residual: float
    jacobian_fd_relative_error: float
    near_discriminant: bool
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return self.status == "OAK_PASS_SOFTWARE_FIXTURE"

    def to_dict(self) -> dict[str, object]:
        return {
            "root_count": self.root_count,
            "max_root_residual": self.max_root_residual,
            "minimum_derivative": self.minimum_derivative,
            "maximum_reciprocal_derivative": self.maximum_reciprocal_derivative,
            "projective_scaling_residual": self.projective_scaling_residual,
            "jacobian_fd_relative_error": self.jacobian_fd_relative_error,
            "near_discriminant": self.near_discriminant,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_rootflow(
    coefficients: npt.ArrayLike,
    *,
    singularity_tolerance: float = 1e-8,
    finite_difference_step: float = 1e-7,
    jacobian_relative_tolerance: float = 1e-5,
) -> RootFlowAudit:
    coeffs = _coefficients(coefficients)
    rr = roots(coeffs)
    conditions = root_conditions(coeffs, rr, singularity_tolerance=singularity_tolerance)
    analytic = root_jacobian(
        coeffs,
        rr,
        singularity_tolerance=min(singularity_tolerance, 1e-12),
    )
    numeric = finite_difference_root_jacobian(coeffs, step=finite_difference_step)
    fd_error = float(
        np.linalg.norm(analytic - numeric)
        / max(np.linalg.norm(numeric), np.finfo(float).eps)
    )
    projective = float(
        np.max(
            np.abs(
                projective_scaling_residual(
                    coeffs,
                    rr,
                    singularity_tolerance=min(singularity_tolerance, 1e-12),
                )
            )
        )
    )
    near = any(item.near_singular for item in conditions)
    max_residual = max(item.residual for item in conditions)
    min_derivative = min(item.derivative_magnitude for item in conditions)
    max_reciprocal = max(item.reciprocal_derivative for item in conditions)

    if near:
        status = "OAK_WARN_NEAR_DISCRIMINANT"
    elif fd_error > jacobian_relative_tolerance:
        status = "OAK_WARN_JACOBIAN_CHECK"
    elif max_residual > 1e-8 or projective > 1e-8:
        status = "OAK_WARN_NUMERICAL_RESIDUAL"
    else:
        status = "OAK_PASS_SOFTWARE_FIXTURE"

    return RootFlowAudit(
        root_count=rr.size,
        max_root_residual=float(max_residual),
        minimum_derivative=float(min_derivative),
        maximum_reciprocal_derivative=float(max_reciprocal),
        projective_scaling_residual=projective,
        jacobian_fd_relative_error=fd_error,
        near_discriminant=near,
        status=status,
    )
