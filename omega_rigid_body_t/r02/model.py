"""Typed rigid-body model, invariants, forcing and stability."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from typing import Callable, Sequence

from .linalg import Quaternion, Vector3, cross, dot, qrotate, vector3

TorqueFunction = Callable[[float, Vector3, Quaternion], Vector3]


@dataclass(frozen=True)
class PrincipalMoments:
    i1: float
    i2: float
    i3: float

    def __post_init__(self) -> None:
        values = (self.i1, self.i2, self.i3)
        if not all(isfinite(value) and value > 0.0 for value in values):
            raise ValueError("principal moments must be finite and positive")
        if not self.i1 < self.i2 < self.i3:
            raise ValueError("R0.2 requires ordered distinct moments I1 < I2 < I3")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def angular_momentum_body(self, omega: Sequence[float]) -> Vector3:
        w1, w2, w3 = vector3(omega)
        return (self.i1 * w1, self.i2 * w2, self.i3 * w3)

    def angular_velocity_from_momentum(self, momentum: Sequence[float]) -> Vector3:
        m1, m2, m3 = vector3(momentum)
        return (m1 / self.i1, m2 / self.i2, m3 / self.i3)


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
class StabilityMode:
    axis: int
    angular_speed: float
    stable: bool
    rate: float
    eigenvalues: tuple[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BalanceReport:
    energy_change: float
    accumulated_work: float
    energy_balance_residual: float
    angular_momentum_change_inertial: Vector3
    accumulated_angular_impulse_inertial: Vector3
    angular_impulse_balance_residual: Vector3

    def to_dict(self) -> dict[str, object]:
        return {
            "energy_change": self.energy_change,
            "accumulated_work": self.accumulated_work,
            "energy_balance_residual": self.energy_balance_residual,
            "angular_momentum_change_inertial": list(self.angular_momentum_change_inertial),
            "accumulated_angular_impulse_inertial": list(self.accumulated_angular_impulse_inertial),
            "angular_impulse_balance_residual": list(self.angular_impulse_balance_residual),
        }


def invariants(model: PrincipalMoments, omega: Sequence[float]) -> Invariants:
    w1, w2, w3 = vector3(omega)
    energy = 0.5 * (model.i1 * w1 * w1 + model.i2 * w2 * w2 + model.i3 * w3 * w3)
    momentum_squared = (
        model.i1 * model.i1 * w1 * w1
        + model.i2 * model.i2 * w2 * w2
        + model.i3 * model.i3 * w3 * w3
    )
    return Invariants(energy, momentum_squared)


def euler_rhs(
    model: PrincipalMoments,
    omega: Sequence[float],
    torque_body: Sequence[float] = (0.0, 0.0, 0.0),
) -> Vector3:
    w1, w2, w3 = vector3(omega)
    t1, t2, t3 = vector3(torque_body)
    return (
        ((model.i2 - model.i3) * w2 * w3 + t1) / model.i1,
        ((model.i3 - model.i1) * w3 * w1 + t2) / model.i2,
        ((model.i1 - model.i2) * w1 * w2 + t3) / model.i3,
    )


def momentum_rhs(model: PrincipalMoments, momentum: Sequence[float]) -> Vector3:
    m = vector3(momentum)
    omega = model.angular_velocity_from_momentum(m)
    return cross(m, omega)


def effective_torque(
    time: float,
    omega: Vector3,
    quaternion: Quaternion,
    torque: TorqueFunction | None,
    damping: float,
) -> Vector3:
    if damping < 0.0 or not isfinite(damping):
        raise ValueError("damping must be finite and non-negative")
    external = (0.0, 0.0, 0.0) if torque is None else vector3(torque(time, omega, quaternion))
    return (
        external[0] - damping * omega[0],
        external[1] - damping * omega[1],
        external[2] - damping * omega[2],
    )


def inertial_angular_momentum(model: PrincipalMoments, omega: Vector3, quaternion: Quaternion) -> Vector3:
    return qrotate(quaternion, model.angular_momentum_body(omega))


def principal_axis_stability(model: PrincipalMoments, axis: int, angular_speed: float) -> StabilityMode:
    if axis not in (1, 2, 3):
        raise ValueError("axis must be 1, 2, or 3")
    if not isfinite(angular_speed):
        raise ValueError("angular_speed must be finite")
    speed = abs(angular_speed)
    if axis == 1:
        rate = speed * sqrt((model.i2 - model.i1) * (model.i3 - model.i1) / (model.i2 * model.i3))
        return StabilityMode(1, angular_speed, True, rate, (f"+{rate}i", f"-{rate}i"))
    if axis == 2:
        rate = speed * sqrt((model.i2 - model.i1) * (model.i3 - model.i2) / (model.i1 * model.i3))
        return StabilityMode(2, angular_speed, False, rate, (f"+{rate}", f"-{rate}"))
    rate = speed * sqrt((model.i3 - model.i1) * (model.i3 - model.i2) / (model.i1 * model.i2))
    return StabilityMode(3, angular_speed, True, rate, (f"+{rate}i", f"-{rate}i"))


def work_rate(torque_body: Vector3, omega: Vector3) -> float:
    return dot(torque_body, omega)
