"""Ω-RIGID-BODY-T: exact and OAK-cross-checked triaxial Euler-top kernel."""

from .elliptic import complete_elliptic_k, jacobi_sncndn
from .euler_top import (
    EllipticTopParameters,
    Invariants,
    PrincipalInertia,
    analytic_omega,
    body_cone_angles,
    classify_regime,
    elliptic_parameters,
    euler_rhs,
    integrate_orientation_quaternion,
    integrate_rk4,
    invariants_from_state,
    precession_rate,
    quaternion_to_matrix,
    sample_analytic,
    separatrix_omega,
)
from .oak import OAKReport, run_oak_benchmarks

__all__ = [
    "EllipticTopParameters",
    "Invariants",
    "OAKReport",
    "PrincipalInertia",
    "analytic_omega",
    "body_cone_angles",
    "classify_regime",
    "complete_elliptic_k",
    "elliptic_parameters",
    "euler_rhs",
    "integrate_orientation_quaternion",
    "integrate_rk4",
    "invariants_from_state",
    "jacobi_sncndn",
    "precession_rate",
    "quaternion_to_matrix",
    "run_oak_benchmarks",
    "sample_analytic",
    "separatrix_omega",
]

__version__ = "0.1.0"
