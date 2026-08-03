"""Exact and numerical torque-free triaxial rigid-body dynamics.

The exact branches use Jacobi elliptic functions and assume ordered principal
moments ``I1 < I2 < I3``. The arbitrary-state RK4 solver is independent of
the analytic branch and is used as an OAK cross-check.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, atan2, isfinite, sqrt
from typing import Callable, Iterable, Sequence

from .elliptic import complete_elliptic_k, jacobi_sncndn

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]


@dataclass(frozen=True)
class PrincipalInertia:
    i1: float
    i2: float
    i3: float

    def __post_init__(self) -> None:
        if not all(isfinite(value) and value > 0.0 for value in (self.i1, self.i2, self.i3)):
            raise ValueError("principal inertias must be finite and positive")
        if not self.i1 < self.i2 < self.i3:
            raise ValueError("R0.1 requires ordered distinct moments I1 < I2 < I3")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class Invariants:
    energy: float
    angular_momentum_squared: float

    @property
    def angular_momentum(self) -> float:
        return sqrt(self.angular_momentum_squared)

    def to_dict(self) -> dict[str, float]:
        return {
            "energy": self.energy,
            "angular_momentum_squared": self.angular_momentum_squared,
            "angular_momentum": self.angular_momentum,
        }


@dataclass(frozen=True)
class EllipticTopParameters:
    regime: str
    amplitude1: float
    amplitude2: float
    amplitude3: float
    frequency: float
    parameter_m: float
    period: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


@dataclass(frozen=True)
class Sample:
    time: float
    omega: Vector3
    energy_residual: float
    momentum_squared_residual: float

    def to_dict(self) -> dict[str, object]:
        return {
            "time": self.time,
            "omega": list(self.omega),
            "energy_residual": self.energy_residual,
            "momentum_squared_residual": self.momentum_squared_residual,
        }


def invariants_from_state(inertia: PrincipalInertia, omega: Sequence[float]) -> Invariants:
    w1, w2, w3 = _vector3(omega)
    energy = 0.5 * (inertia.i1 * w1 * w1 + inertia.i2 * w2 * w2 + inertia.i3 * w3 * w3)
    momentum_squared = (
        inertia.i1**2 * w1 * w1
        + inertia.i2**2 * w2 * w2
        + inertia.i3**2 * w3 * w3
    )
    return Invariants(energy=energy, angular_momentum_squared=momentum_squared)


def admissible_energy_interval(inertia: PrincipalInertia, angular_momentum_squared: float) -> tuple[float, float]:
    if not isfinite(angular_momentum_squared) or angular_momentum_squared <= 0.0:
        raise ValueError("angular_momentum_squared must be finite and positive")
    return (
        angular_momentum_squared / (2.0 * inertia.i3),
        angular_momentum_squared / (2.0 * inertia.i1),
    )


def classify_regime(
    inertia: PrincipalInertia,
    invariants: Invariants,
    *,
    tolerance: float = 1e-12,
) -> str:
    _validate_invariants(inertia, invariants, tolerance=tolerance)
    threshold = invariants.angular_momentum_squared / (2.0 * inertia.i2)
    scale = max(1.0, abs(invariants.energy), abs(threshold))
    if abs(invariants.energy - threshold) <= tolerance * scale:
        return "separatrix_intermediate_axis"
    if invariants.energy < threshold:
        return "stable_axis_3"
    return "stable_axis_1"


def elliptic_parameters(
    inertia: PrincipalInertia,
    invariants: Invariants,
    *,
    tolerance: float = 1e-12,
) -> EllipticTopParameters:
    regime = classify_regime(inertia, invariants, tolerance=tolerance)
    if regime == "separatrix_intermediate_axis":
        raise ValueError("the separatrix has a hyperbolic, not finite-period elliptic, parameterization")

    i1, i2, i3 = inertia.i1, inertia.i2, inertia.i3
    energy = invariants.energy
    l2 = invariants.angular_momentum_squared

    amplitude1 = sqrt(max(0.0, (2.0 * energy * i3 - l2) / (i1 * (i3 - i1))))
    amplitude3 = sqrt(max(0.0, (l2 - 2.0 * energy * i1) / (i3 * (i3 - i1))))

    if regime == "stable_axis_3":
        amplitude2 = sqrt(max(0.0, (2.0 * energy * i3 - l2) / (i2 * (i3 - i2))))
        frequency = sqrt((i3 - i2) * (l2 - 2.0 * energy * i1) / (i1 * i2 * i3))
        parameter_m = (
            (i2 - i1) * (2.0 * energy * i3 - l2)
            / ((i3 - i2) * (l2 - 2.0 * energy * i1))
        )
    else:
        amplitude2 = sqrt(max(0.0, (l2 - 2.0 * energy * i1) / (i2 * (i2 - i1))))
        frequency = sqrt((i2 - i1) * (2.0 * energy * i3 - l2) / (i1 * i2 * i3))
        parameter_m = (
            (i3 - i2) * (l2 - 2.0 * energy * i1)
            / ((i2 - i1) * (2.0 * energy * i3 - l2))
        )

    parameter_m = _clamp_unit_interval(parameter_m, tolerance=tolerance)
    period = 4.0 * complete_elliptic_k(parameter_m) / frequency
    return EllipticTopParameters(
        regime=regime,
        amplitude1=amplitude1,
        amplitude2=amplitude2,
        amplitude3=amplitude3,
        frequency=frequency,
        parameter_m=parameter_m,
        period=period,
    )


def analytic_omega(
    time: float,
    parameters: EllipticTopParameters,
    *,
    phase: float = 0.0,
) -> Vector3:
    """Evaluate a canonical real branch of the exact Euler-top solution."""

    u = parameters.frequency * time + phase
    sn, cn, dn = jacobi_sncndn(u, parameters.parameter_m)
    if parameters.regime == "stable_axis_3":
        return (
            parameters.amplitude1 * cn,
            parameters.amplitude2 * sn,
            parameters.amplitude3 * dn,
        )
    if parameters.regime == "stable_axis_1":
        return (
            parameters.amplitude1 * dn,
            parameters.amplitude2 * sn,
            parameters.amplitude3 * cn,
        )
    raise ValueError(f"unsupported elliptic regime: {parameters.regime}")


def separatrix_parameters(inertia: PrincipalInertia, angular_momentum: float) -> dict[str, float]:
    if not isfinite(angular_momentum) or angular_momentum <= 0.0:
        raise ValueError("angular_momentum must be finite and positive")
    i1, i2, i3 = inertia.i1, inertia.i2, inertia.i3
    l2 = angular_momentum * angular_momentum
    return {
        "amplitude1": sqrt(l2 * (i3 - i2) / (i1 * i2 * (i3 - i1))),
        "amplitude2": angular_momentum / i2,
        "amplitude3": sqrt(l2 * (i2 - i1) / (i2 * i3 * (i3 - i1))),
        "growth_rate": sqrt(l2 * (i3 - i2) * (i2 - i1) / (i1 * i2 * i2 * i3)),
    }


def separatrix_omega(
    time: float,
    inertia: PrincipalInertia,
    angular_momentum: float,
    *,
    center_time: float = 0.0,
) -> Vector3:
    params = separatrix_parameters(inertia, angular_momentum)
    u = params["growth_rate"] * (time - center_time)
    sn, cn, _ = jacobi_sncndn(u, 1.0)
    return (
        params["amplitude1"] * cn,
        params["amplitude2"] * sn,
        params["amplitude3"] * cn,
    )


def euler_rhs(inertia: PrincipalInertia, omega: Sequence[float]) -> Vector3:
    w1, w2, w3 = _vector3(omega)
    return (
        (inertia.i2 - inertia.i3) * w2 * w3 / inertia.i1,
        (inertia.i3 - inertia.i1) * w3 * w1 / inertia.i2,
        (inertia.i1 - inertia.i2) * w1 * w2 / inertia.i3,
    )


def integrate_rk4(
    inertia: PrincipalInertia,
    initial_omega: Sequence[float],
    times: Iterable[float],
) -> list[Vector3]:
    """Integrate arbitrary initial data at monotonically increasing sample times."""

    requested_times = [float(value) for value in times]
    if not requested_times:
        return []
    if requested_times[0] < 0.0:
        raise ValueError("R0.1 RK4 sampling requires non-negative times")
    if any(right < left for left, right in zip(requested_times, requested_times[1:])):
        raise ValueError("times must be monotonically increasing")

    state = _vector3(initial_omega)
    current_time = 0.0
    result: list[Vector3] = []
    for target_time in requested_times:
        interval = target_time - current_time
        if interval > 0.0:
            characteristic = max(1.0, sum(abs(value) for value in state))
            steps = max(1, int(interval * characteristic * 400.0) + 1)
            dt = interval / steps
            for _ in range(steps):
                state = _rk4_step(lambda value: euler_rhs(inertia, value), state, dt)
            current_time = target_time
        result.append(state)
    return result


def invariant_residuals(
    inertia: PrincipalInertia,
    omega: Sequence[float],
    reference: Invariants,
) -> tuple[float, float]:
    observed = invariants_from_state(inertia, omega)
    energy_scale = max(1.0, abs(reference.energy))
    momentum_scale = max(1.0, abs(reference.angular_momentum_squared))
    return (
        (observed.energy - reference.energy) / energy_scale,
        (observed.angular_momentum_squared - reference.angular_momentum_squared) / momentum_scale,
    )


def sample_analytic(
    inertia: PrincipalInertia,
    invariants: Invariants,
    times: Iterable[float],
    *,
    phase: float = 0.0,
) -> list[Sample]:
    parameters = elliptic_parameters(inertia, invariants)
    samples = []
    for time in times:
        omega = analytic_omega(float(time), parameters, phase=phase)
        energy_residual, momentum_residual = invariant_residuals(inertia, omega, invariants)
        samples.append(
            Sample(
                time=float(time),
                omega=omega,
                energy_residual=energy_residual,
                momentum_squared_residual=momentum_residual,
            )
        )
    return samples


def body_cone_angles(
    inertia: PrincipalInertia,
    omega: Sequence[float],
    angular_momentum: float,
) -> tuple[float, float]:
    """Return ``(theta, psi)`` for a ZXZ convention with inertial z along L."""

    if angular_momentum <= 0.0:
        raise ValueError("angular_momentum must be positive")
    w1, w2, w3 = _vector3(omega)
    cosine_theta = inertia.i3 * w3 / angular_momentum
    theta = acos(max(-1.0, min(1.0, cosine_theta)))
    psi = atan2(inertia.i1 * w1, inertia.i2 * w2)
    return theta, psi


def precession_rate(
    inertia: PrincipalInertia,
    omega: Sequence[float],
    angular_momentum: float,
) -> float:
    """Return the exact Euler-angle precession rate around inertial L."""

    if angular_momentum <= 0.0:
        raise ValueError("angular_momentum must be positive")
    w1, w2, _ = _vector3(omega)
    denominator = inertia.i1**2 * w1 * w1 + inertia.i2**2 * w2 * w2
    if denominator == 0.0:
        raise ValueError("precession rate is coordinate-singular on the selected Euler-angle pole")
    numerator = inertia.i1 * w1 * w1 + inertia.i2 * w2 * w2
    return angular_momentum * numerator / denominator


def integrate_orientation_quaternion(
    omega_function: Callable[[float], Vector3],
    times: Iterable[float],
    *,
    initial: Quaternion = (1.0, 0.0, 0.0, 0.0),
) -> list[Quaternion]:
    """Reconstruct body-to-inertial orientation from body-frame angular velocity."""

    requested_times = [float(value) for value in times]
    if not requested_times:
        return []
    if requested_times[0] < 0.0 or any(
        right < left for left, right in zip(requested_times, requested_times[1:])
    ):
        raise ValueError("times must be non-negative and monotonically increasing")

    q = _normalize_quaternion(initial)
    current_time = 0.0
    output: list[Quaternion] = []
    for target_time in requested_times:
        interval = target_time - current_time
        if interval > 0.0:
            midpoint_omega = omega_function(current_time + 0.5 * interval)
            characteristic = max(1.0, sum(abs(value) for value in midpoint_omega))
            steps = max(1, int(interval * characteristic * 500.0) + 1)
            dt = interval / steps
            for _ in range(steps):
                q = _quaternion_rk4_step(q, current_time, dt, omega_function)
                current_time += dt
        output.append(q)
    return output


def quaternion_to_matrix(q: Sequence[float]) -> tuple[tuple[float, float, float], ...]:
    w, x, y, z = _normalize_quaternion(q)
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
        (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
        (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)),
    )


def _validate_invariants(
    inertia: PrincipalInertia,
    invariants: Invariants,
    *,
    tolerance: float,
) -> None:
    if not isfinite(invariants.energy) or invariants.energy <= 0.0:
        raise ValueError("energy must be finite and positive")
    if not isfinite(invariants.angular_momentum_squared) or invariants.angular_momentum_squared <= 0.0:
        raise ValueError("angular_momentum_squared must be finite and positive")
    minimum, maximum = admissible_energy_interval(inertia, invariants.angular_momentum_squared)
    scale = max(1.0, abs(minimum), abs(maximum), abs(invariants.energy))
    if invariants.energy < minimum - tolerance * scale or invariants.energy > maximum + tolerance * scale:
        raise ValueError("energy is outside the torque-free admissible interval at fixed angular momentum")


def _clamp_unit_interval(value: float, *, tolerance: float) -> float:
    if value < -tolerance or value > 1.0 + tolerance:
        raise ArithmeticError(f"derived elliptic parameter is outside [0,1]: {value}")
    return max(0.0, min(1.0, value))


def _vector3(values: Sequence[float]) -> Vector3:
    if len(values) != 3:
        raise ValueError("expected exactly three components")
    vector = tuple(float(value) for value in values)
    if not all(isfinite(value) for value in vector):
        raise ValueError("vector components must be finite")
    return vector  # type: ignore[return-value]


def _rk4_step(rhs: Callable[[Vector3], Vector3], state: Vector3, dt: float) -> Vector3:
    k1 = rhs(state)
    k2 = rhs(tuple(state[i] + 0.5 * dt * k1[i] for i in range(3)))
    k3 = rhs(tuple(state[i] + 0.5 * dt * k2[i] for i in range(3)))
    k4 = rhs(tuple(state[i] + dt * k3[i] for i in range(3)))
    return tuple(
        state[i] + dt * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0
        for i in range(3)
    )  # type: ignore[return-value]


def _quaternion_product(left: Quaternion, right: Quaternion) -> Quaternion:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def _quaternion_derivative(q: Quaternion, omega: Vector3) -> Quaternion:
    product = _quaternion_product(q, (0.0, *omega))
    return tuple(0.5 * value for value in product)  # type: ignore[return-value]


def _quaternion_rk4_step(
    q: Quaternion,
    time: float,
    dt: float,
    omega_function: Callable[[float], Vector3],
) -> Quaternion:
    def shifted(base: Quaternion, slope: Quaternion, factor: float) -> Quaternion:
        return tuple(base[i] + factor * slope[i] for i in range(4))  # type: ignore[return-value]

    k1 = _quaternion_derivative(q, omega_function(time))
    k2 = _quaternion_derivative(shifted(q, k1, 0.5 * dt), omega_function(time + 0.5 * dt))
    k3 = _quaternion_derivative(shifted(q, k2, 0.5 * dt), omega_function(time + 0.5 * dt))
    k4 = _quaternion_derivative(shifted(q, k3, dt), omega_function(time + dt))
    updated = tuple(
        q[i] + dt * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0
        for i in range(4)
    )
    return _normalize_quaternion(updated)


def _normalize_quaternion(q: Sequence[float]) -> Quaternion:
    if len(q) != 4:
        raise ValueError("quaternion must have four components")
    values = tuple(float(value) for value in q)
    norm = sqrt(sum(value * value for value in values))
    if norm == 0.0 or not isfinite(norm):
        raise ValueError("quaternion norm must be finite and non-zero")
    return tuple(value / norm for value in values)  # type: ignore[return-value]
