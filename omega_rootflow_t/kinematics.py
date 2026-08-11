"""Second-order parameter kinematics for Ω-ROOTFLOW-T∞ R0.5.

For a smooth coefficient family ``P(z,t)`` and a simple root ``r(t)``:

    r'  = -P_t / P_z
    r'' = -(P_zz r'^2 + 2 P_zt r' + P_tt) / P_z.

The formulas are exact local implicit-differentiation identities at simple
roots.  Taylor prediction built from them remains a local approximation and is
explicitly separated from nonlinear root solving.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .core import _coefficients, derivative_value, polynomial_value, roots

ComplexArray = npt.NDArray[np.complex128]


def _parameter_vector(values: npt.ArrayLike, shape: tuple[int, ...], name: str) -> ComplexArray:
    array = np.asarray(values, dtype=np.complex128)
    if array.shape != shape:
        raise ValueError(f"{name} must match the coefficient vector shape")
    if not np.all(np.isfinite(array.real)) or not np.all(np.isfinite(array.imag)):
        raise ValueError(f"{name} must be finite")
    return array


def _raw_value(coefficients: ComplexArray, z: complex) -> complex:
    return complex(np.polynomial.polynomial.polyval(z, coefficients))


def _raw_derivative_value(coefficients: ComplexArray, z: complex) -> complex:
    if coefficients.size <= 1:
        return 0j
    derivative = np.arange(1, coefficients.size, dtype=float) * coefficients[1:]
    return complex(np.polynomial.polynomial.polyval(z, derivative))


@dataclass(frozen=True)
class RootKinematicState:
    root: complex
    velocity: complex
    acceleration: complex
    derivative_magnitude: float
    residual: float

    def to_dict(self) -> dict[str, object]:
        def encode(value: complex) -> list[float]:
            return [float(value.real), float(value.imag)]

        return {
            "root": encode(self.root),
            "velocity": encode(self.velocity),
            "acceleration": encode(self.acceleration),
            "derivative_magnitude": self.derivative_magnitude,
            "residual": self.residual,
        }


@dataclass(frozen=True)
class RootKinematics:
    states: tuple[RootKinematicState, ...]
    minimum_derivative: float
    maximum_residual: float
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def roots(self) -> ComplexArray:
        return np.asarray([item.root for item in self.states], dtype=np.complex128)

    @property
    def velocities(self) -> ComplexArray:
        return np.asarray([item.velocity for item in self.states], dtype=np.complex128)

    @property
    def accelerations(self) -> ComplexArray:
        return np.asarray([item.acceleration for item in self.states], dtype=np.complex128)

    def to_dict(self) -> dict[str, object]:
        return {
            "states": [item.to_dict() for item in self.states],
            "minimum_derivative": self.minimum_derivative,
            "maximum_residual": self.maximum_residual,
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def parameter_root_kinematics(
    coefficients: npt.ArrayLike,
    coefficient_velocity: npt.ArrayLike,
    coefficient_acceleration: npt.ArrayLike | None = None,
    root_values: npt.ArrayLike | None = None,
    *,
    singularity_tolerance: float = 1e-12,
) -> RootKinematics:
    """Compute exact local first/second parameter derivatives of simple roots."""
    coeffs = _coefficients(coefficients)
    velocity_coeffs = _parameter_vector(
        coefficient_velocity,
        coeffs.shape,
        "coefficient_velocity",
    )
    acceleration_coeffs = (
        np.zeros_like(coeffs)
        if coefficient_acceleration is None
        else _parameter_vector(
            coefficient_acceleration,
            coeffs.shape,
            "coefficient_acceleration",
        )
    )
    if singularity_tolerance <= 0:
        raise ValueError("singularity_tolerance must be positive")
    rr = roots(coeffs) if root_values is None else np.asarray(root_values, dtype=np.complex128)
    if rr.ndim != 1:
        raise ValueError("root_values must be one-dimensional")

    states: list[RootKinematicState] = []
    for root_value in rr:
        root = complex(root_value)
        p_z = derivative_value(coeffs, root)
        derivative_magnitude = abs(p_z)
        if derivative_magnitude <= singularity_tolerance:
            raise np.linalg.LinAlgError("root kinematics are singular near P_z=0")
        p_t = _raw_value(velocity_coeffs, root)
        root_velocity = -p_t / p_z
        p_zz = derivative_value(coeffs, root, order=2)
        p_zt = _raw_derivative_value(velocity_coeffs, root)
        p_tt = _raw_value(acceleration_coeffs, root)
        root_acceleration = -(
            p_zz * root_velocity**2
            + 2.0 * p_zt * root_velocity
            + p_tt
        ) / p_z
        states.append(
            RootKinematicState(
                root=root,
                velocity=complex(root_velocity),
                acceleration=complex(root_acceleration),
                derivative_magnitude=float(derivative_magnitude),
                residual=float(abs(polynomial_value(coeffs, root))),
            )
        )

    minimum = min((item.derivative_magnitude for item in states), default=float("inf"))
    maximum_residual = max((item.residual for item in states), default=0.0)
    return RootKinematics(
        states=tuple(states),
        minimum_derivative=float(minimum),
        maximum_residual=float(maximum_residual),
        status="OAK_PASS_PARAMETER_KINEMATICS",
    )


def taylor_predict_roots(
    kinematics: RootKinematics,
    delta_parameter: float | complex,
    *,
    order: int = 2,
) -> ComplexArray:
    """Local root prediction of order one or two from a kinematic state."""
    if order not in (1, 2):
        raise ValueError("order must be 1 or 2")
    delta = complex(delta_parameter)
    predicted = kinematics.roots + kinematics.velocities * delta
    if order == 2:
        predicted = predicted + 0.5 * kinematics.accelerations * delta**2
    return np.asarray(predicted, dtype=np.complex128)
