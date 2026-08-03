"""R0.2 quaternion attitude, actuator and deterministic sensor models.

The implementation is a reduced-order research baseline. It is not flight
software, a qualified controller or a substitute for hardware-in-the-loop and
mission-specific stability analysis.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, cos, sin, sqrt
from typing import Any

from .models import Vector3, require_finite
from .orbit import add, cross, norm, scale, subtract


Quaternion = tuple[float, float, float, float]


def quaternion_norm(quaternion: Quaternion) -> float:
    return sqrt(sum(component * component for component in quaternion))


def normalize_quaternion(quaternion: Quaternion) -> Quaternion:
    magnitude = quaternion_norm(quaternion)
    if magnitude <= 0.0:
        raise ValueError("quaternion must be nonzero")
    return tuple(component / magnitude for component in quaternion)  # type: ignore[return-value]


def quaternion_conjugate(quaternion: Quaternion) -> Quaternion:
    return (quaternion[0], -quaternion[1], -quaternion[2], -quaternion[3])


def quaternion_multiply(left: Quaternion, right: Quaternion) -> Quaternion:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def quaternion_from_axis_angle(axis: Vector3, angle_rad: float) -> Quaternion:
    magnitude = norm(axis)
    if magnitude <= 0.0:
        raise ValueError("rotation axis must be nonzero")
    unit = scale(1.0 / magnitude, axis)
    half = 0.5 * angle_rad
    sine = sin(half)
    return normalize_quaternion((cos(half), unit[0] * sine, unit[1] * sine, unit[2] * sine))


def quaternion_from_rotation_vector(rotation_vector_rad: Vector3) -> Quaternion:
    angle = norm(rotation_vector_rad)
    if angle <= 1e-15:
        return normalize_quaternion((1.0, 0.5 * rotation_vector_rad[0], 0.5 * rotation_vector_rad[1], 0.5 * rotation_vector_rad[2]))
    return quaternion_from_axis_angle(rotation_vector_rad, angle)


def rotate_vector(quaternion: Quaternion, vector: Vector3) -> Vector3:
    q = normalize_quaternion(quaternion)
    rotated = quaternion_multiply(quaternion_multiply(q, (0.0, *vector)), quaternion_conjugate(q))
    return (rotated[1], rotated[2], rotated[3])


def quaternion_error(target: Quaternion, current: Quaternion) -> Quaternion:
    error = normalize_quaternion(quaternion_multiply(normalize_quaternion(target), quaternion_conjugate(normalize_quaternion(current))))
    if error[0] < 0.0:
        return tuple(-value for value in error)  # type: ignore[return-value]
    return error


def attitude_error_angle_rad(target: Quaternion, current: Quaternion) -> float:
    error = quaternion_error(target, current)
    return 2.0 * acos(max(-1.0, min(1.0, error[0])))


@dataclass(frozen=True)
class AttitudeState:
    quaternion_body_to_inertial: Quaternion
    angular_velocity_rad_s: Vector3
    wheel_momentum_nms: Vector3 = (0.0, 0.0, 0.0)
    epoch_s: float = 0.0

    def validate(self) -> None:
        require_finite((*self.quaternion_body_to_inertial, *self.angular_velocity_rad_s, *self.wheel_momentum_nms), "attitude state")
        if quaternion_norm(self.quaternion_body_to_inertial) <= 0.0:
            raise ValueError("attitude quaternion must be nonzero")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AttitudeControlConfig:
    inertia_kg_m2: Vector3
    kp_n_m_per_quaternion: Vector3
    kd_n_m_s: Vector3
    max_wheel_torque_n_m: Vector3
    max_wheel_momentum_nms: Vector3
    wheel_friction_per_s: float = 0.0

    def validate(self) -> None:
        if any(value <= 0.0 for value in self.inertia_kg_m2):
            raise ValueError("principal inertias must be positive")
        if any(value < 0.0 for value in (*self.kp_n_m_per_quaternion, *self.kd_n_m_s, *self.max_wheel_torque_n_m, *self.max_wheel_momentum_nms)):
            raise ValueError("controller and wheel limits cannot be negative")
        if self.wheel_friction_per_s < 0.0:
            raise ValueError("wheel friction cannot be negative")


@dataclass(frozen=True)
class GyroModel:
    bias_rad_s: Vector3 = (0.0, 0.0, 0.0)
    noise_std_rad_s: float = 0.0
    seed: int = 2026


@dataclass(frozen=True)
class StarTrackerModel:
    noise_std_rad: float = 0.0
    seed: int = 2027
    cadence_steps: int = 1


@dataclass(frozen=True)
class AttitudeSimulationMetrics:
    initial_error_rad: float
    final_error_rad: float
    maximum_error_rad: float
    maximum_rate_rad_s: float
    maximum_wheel_momentum_fraction: float
    torque_saturation_count: int
    wheel_saturation_count: int
    quaternion_norm_error: float
    safe: bool
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["violations"] = list(self.violations)
        return payload


@dataclass(frozen=True)
class AttitudeSimulationResult:
    states: tuple[AttitudeState, ...]
    metrics: AttitudeSimulationMetrics
    target_quaternion: Quaternion
    deterministic_sensor_digest: tuple[float, ...]

    def to_dict(self, include_states: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "metrics": self.metrics.to_dict(),
            "target_quaternion": self.target_quaternion,
            "deterministic_sensor_digest": self.deterministic_sensor_digest,
            "flight_qualified_claimed": False,
        }
        if include_states:
            payload["states"] = [state.to_dict() for state in self.states]
        return payload


def _bounded(value: float, limit: float) -> tuple[float, bool]:
    if value > limit:
        return limit, True
    if value < -limit:
        return -limit, True
    return value, False


def _deterministic_noise(seed: int, sample_index: int, axis: int) -> float:
    phase = float(seed * 131 + sample_index * 977 + axis * 37)
    return (sin(phase * 0.017453292519943295) + 0.5 * sin(phase * 0.011)) / 1.5


def gyro_measurement(truth_rate_rad_s: Vector3, model: GyroModel, sample_index: int) -> Vector3:
    return tuple(
        truth_rate_rad_s[axis]
        + model.bias_rad_s[axis]
        + model.noise_std_rad_s * _deterministic_noise(model.seed, sample_index, axis)
        for axis in range(3)
    )  # type: ignore[return-value]


def star_tracker_measurement(truth_quaternion: Quaternion, model: StarTrackerModel, sample_index: int) -> Quaternion | None:
    if model.cadence_steps <= 0:
        raise ValueError("star tracker cadence must be positive")
    if sample_index % model.cadence_steps != 0:
        return None
    noise_vector = tuple(
        model.noise_std_rad * _deterministic_noise(model.seed, sample_index, axis)
        for axis in range(3)
    )
    error = quaternion_from_rotation_vector(noise_vector)  # type: ignore[arg-type]
    return normalize_quaternion(quaternion_multiply(error, truth_quaternion))


def pd_wheel_torque(
    state: AttitudeState,
    target_quaternion: Quaternion,
    target_rate_rad_s: Vector3,
    config: AttitudeControlConfig,
) -> tuple[Vector3, int]:
    error = quaternion_error(target_quaternion, state.quaternion_body_to_inertial)
    rate_error = subtract(target_rate_rad_s, state.angular_velocity_rad_s)
    requested = tuple(
        2.0 * config.kp_n_m_per_quaternion[axis] * error[axis + 1]
        + config.kd_n_m_s[axis] * rate_error[axis]
        for axis in range(3)
    )
    limited: list[float] = []
    saturation_count = 0
    for axis in range(3):
        value, saturated = _bounded(requested[axis], config.max_wheel_torque_n_m[axis])
        limited.append(value)
        saturation_count += int(saturated)
    return (limited[0], limited[1], limited[2]), saturation_count


def magnetic_dipole_torque(dipole_a_m2: Vector3, magnetic_field_t: Vector3) -> Vector3:
    return cross(dipole_a_m2, magnetic_field_t)


def rigid_body_angular_acceleration(
    angular_velocity_rad_s: Vector3,
    applied_torque_n_m: Vector3,
    inertia_kg_m2: Vector3,
) -> Vector3:
    angular_momentum = tuple(inertia_kg_m2[axis] * angular_velocity_rad_s[axis] for axis in range(3))
    gyroscopic = cross(angular_velocity_rad_s, angular_momentum)  # type: ignore[arg-type]
    return tuple(
        (applied_torque_n_m[axis] - gyroscopic[axis]) / inertia_kg_m2[axis]
        for axis in range(3)
    )  # type: ignore[return-value]


def _quaternion_derivative(quaternion: Quaternion, angular_velocity_rad_s: Vector3) -> Quaternion:
    return tuple(0.5 * value for value in quaternion_multiply(quaternion, (0.0, *angular_velocity_rad_s)))  # type: ignore[return-value]


def attitude_step(
    state: AttitudeState,
    dt_s: float,
    body_torque_n_m: Vector3,
    config: AttitudeControlConfig,
) -> tuple[AttitudeState, int]:
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    config.validate()
    state.validate()

    acceleration_0 = rigid_body_angular_acceleration(state.angular_velocity_rad_s, body_torque_n_m, config.inertia_kg_m2)
    mid_rate = add(state.angular_velocity_rad_s, scale(0.5 * dt_s, acceleration_0))
    acceleration_mid = rigid_body_angular_acceleration(mid_rate, body_torque_n_m, config.inertia_kg_m2)
    next_rate = add(state.angular_velocity_rad_s, scale(dt_s, acceleration_mid))

    q_dot_0 = _quaternion_derivative(state.quaternion_body_to_inertial, state.angular_velocity_rad_s)
    mid_quaternion = normalize_quaternion(tuple(
        state.quaternion_body_to_inertial[index] + 0.5 * dt_s * q_dot_0[index]
        for index in range(4)
    ))
    q_dot_mid = _quaternion_derivative(mid_quaternion, mid_rate)
    next_quaternion = normalize_quaternion(tuple(
        state.quaternion_body_to_inertial[index] + dt_s * q_dot_mid[index]
        for index in range(4)
    ))

    wheel_saturation_count = 0
    next_momentum: list[float] = []
    for axis in range(3):
        raw = (
            state.wheel_momentum_nms[axis] - body_torque_n_m[axis] * dt_s
        ) * max(0.0, 1.0 - config.wheel_friction_per_s * dt_s)
        value, saturated = _bounded(raw, config.max_wheel_momentum_nms[axis])
        next_momentum.append(value)
        wheel_saturation_count += int(saturated)
    next_state = AttitudeState(
        next_quaternion,
        next_rate,
        (next_momentum[0], next_momentum[1], next_momentum[2]),
        state.epoch_s + dt_s,
    )
    next_state.validate()
    return next_state, wheel_saturation_count


def simulate_attitude_control(
    initial_state: AttitudeState,
    target_quaternion: Quaternion,
    duration_s: float,
    step_s: float,
    config: AttitudeControlConfig,
    *,
    target_rate_rad_s: Vector3 = (0.0, 0.0, 0.0),
    disturbance_torque_n_m: Vector3 = (0.0, 0.0, 0.0),
    gyro: GyroModel = GyroModel(),
    star_tracker: StarTrackerModel = StarTrackerModel(),
) -> AttitudeSimulationResult:
    if duration_s <= 0.0 or step_s <= 0.0:
        raise ValueError("duration and step must be positive")
    initial_state.validate()
    config.validate()
    target = normalize_quaternion(target_quaternion)
    states = [initial_state]
    state = initial_state
    remaining = duration_s
    sample_index = 0
    torque_saturation_count = 0
    wheel_saturation_count = 0
    sensor_digest: list[float] = []

    while remaining > 1e-12:
        dt = min(step_s, remaining)
        measured_rate = gyro_measurement(state.angular_velocity_rad_s, gyro, sample_index)
        measured_quaternion = star_tracker_measurement(state.quaternion_body_to_inertial, star_tracker, sample_index)
        control_state = AttitudeState(
            measured_quaternion or state.quaternion_body_to_inertial,
            measured_rate,
            state.wheel_momentum_nms,
            state.epoch_s,
        )
        control_torque, saturations = pd_wheel_torque(control_state, target, target_rate_rad_s, config)
        torque_saturation_count += saturations
        total_torque = add(control_torque, disturbance_torque_n_m)
        state, wheel_saturations = attitude_step(state, dt, total_torque, config)
        wheel_saturation_count += wheel_saturations
        states.append(state)
        sensor_digest.extend((*measured_rate, *(measured_quaternion or state.quaternion_body_to_inertial)))
        remaining -= dt
        sample_index += 1

    errors = [attitude_error_angle_rad(target, item.quaternion_body_to_inertial) for item in states]
    max_rate = max(norm(item.angular_velocity_rad_s) for item in states)
    momentum_fractions = [
        abs(item.wheel_momentum_nms[axis]) / max(config.max_wheel_momentum_nms[axis], 1e-30)
        for item in states
        for axis in range(3)
    ]
    norm_error = max(abs(quaternion_norm(item.quaternion_body_to_inertial) - 1.0) for item in states)
    violations: list[str] = []
    if max(momentum_fractions) >= 1.0:
        violations.append("reaction-wheel momentum saturation reached")
    if errors[-1] >= errors[0]:
        violations.append("closed-loop attitude error did not decrease")
    if norm_error > 1e-10:
        violations.append("quaternion normalization tolerance exceeded")
    metrics = AttitudeSimulationMetrics(
        initial_error_rad=errors[0],
        final_error_rad=errors[-1],
        maximum_error_rad=max(errors),
        maximum_rate_rad_s=max_rate,
        maximum_wheel_momentum_fraction=max(momentum_fractions),
        torque_saturation_count=torque_saturation_count,
        wheel_saturation_count=wheel_saturation_count,
        quaternion_norm_error=norm_error,
        safe=not violations,
        violations=tuple(violations),
    )
    return AttitudeSimulationResult(
        states=tuple(states),
        metrics=metrics,
        target_quaternion=target,
        deterministic_sensor_digest=tuple(round(value, 15) for value in sensor_digest[:32]),
    )
