"""R0.2 orbital perturbation models for Ω-SPACE-HG-T∞.

Transparent reduced-order research baselines. They are not operational
ephemeris, conjunction-assessment, navigation or flight-dynamics software.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import acos, atan2, cos, exp, pi, sin, sqrt
from typing import Callable, Iterable

from .models import OrbitState, Vector3, require_finite
from .orbit import add, cross, dot, norm, scale, subtract, two_body_acceleration


@dataclass(frozen=True)
class PerturbationConfig:
    mu_m3_s2: float
    body_radius_m: float
    j2: float = 0.0
    body_rotation_rad_s: float = 0.0
    drag_coefficient: float = 0.0
    drag_area_m2: float = 0.0
    mass_kg: float = 1.0
    reference_density_kg_m3: float = 0.0
    reference_altitude_m: float = 0.0
    density_scale_height_m: float = 1.0
    solar_pressure_n_m2: float = 0.0
    reflectivity_coefficient: float = 0.0
    solar_area_m2: float = 0.0
    sun_direction_inertial: Vector3 = (1.0, 0.0, 0.0)

    def validate(self) -> None:
        if self.mu_m3_s2 <= 0.0 or self.body_radius_m <= 0.0 or self.mass_kg <= 0.0:
            raise ValueError("mu, body radius and mass must be positive")
        if self.density_scale_height_m <= 0.0:
            raise ValueError("density scale height must be positive")
        if self.drag_coefficient < 0.0 or self.drag_area_m2 < 0.0:
            raise ValueError("drag parameters cannot be negative")
        if self.solar_pressure_n_m2 < 0.0 or self.solar_area_m2 < 0.0:
            raise ValueError("solar-radiation-pressure parameters cannot be negative")
        if norm(self.sun_direction_inertial) <= 0.0:
            raise ValueError("sun direction must be nonzero")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OsculatingElements:
    semimajor_axis_m: float
    eccentricity: float
    inclination_rad: float
    raan_rad: float
    argument_of_periapsis_rad: float
    true_anomaly_rad: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _unit(vector: Vector3) -> Vector3:
    magnitude = norm(vector)
    if magnitude <= 0.0:
        raise ValueError("cannot normalize a zero vector")
    return scale(1.0 / magnitude, vector)


def j2_acceleration(position_m: Vector3, config: PerturbationConfig) -> Vector3:
    """First-order J2 acceleration in a body-equatorial inertial frame."""

    if config.j2 == 0.0:
        return (0.0, 0.0, 0.0)
    x, y, z = position_m
    radius = norm(position_m)
    if radius <= config.body_radius_m:
        raise ValueError("state lies at or below the reference body surface")
    z2_over_r2 = (z / radius) ** 2
    factor = 1.5 * config.j2 * config.mu_m3_s2 * config.body_radius_m**2 / radius**5
    return (
        factor * x * (5.0 * z2_over_r2 - 1.0),
        factor * y * (5.0 * z2_over_r2 - 1.0),
        factor * z * (5.0 * z2_over_r2 - 3.0),
    )


def exponential_density(position_m: Vector3, config: PerturbationConfig) -> float:
    altitude_m = norm(position_m) - config.body_radius_m
    if altitude_m < 0.0:
        raise ValueError("altitude cannot be negative")
    if config.reference_density_kg_m3 <= 0.0:
        return 0.0
    exponent = -(altitude_m - config.reference_altitude_m) / config.density_scale_height_m
    return config.reference_density_kg_m3 * exp(max(-700.0, min(700.0, exponent)))


def drag_acceleration(state: OrbitState, config: PerturbationConfig) -> Vector3:
    if config.drag_coefficient == 0.0 or config.drag_area_m2 == 0.0:
        return (0.0, 0.0, 0.0)
    density = exponential_density(state.position_m, config)
    atmosphere_velocity = cross((0.0, 0.0, config.body_rotation_rad_s), state.position_m)
    relative_velocity = subtract(state.velocity_m_s, atmosphere_velocity)
    speed = norm(relative_velocity)
    if density == 0.0 or speed == 0.0:
        return (0.0, 0.0, 0.0)
    coefficient = -0.5 * density * config.drag_coefficient * config.drag_area_m2 * speed / config.mass_kg
    return scale(coefficient, relative_velocity)


def solar_radiation_pressure_acceleration(
    state: OrbitState,
    config: PerturbationConfig,
    *,
    illuminated: bool = True,
) -> Vector3:
    del state
    if (
        not illuminated
        or config.solar_pressure_n_m2 == 0.0
        or config.reflectivity_coefficient == 0.0
        or config.solar_area_m2 == 0.0
    ):
        return (0.0, 0.0, 0.0)
    magnitude = (
        config.solar_pressure_n_m2
        * config.reflectivity_coefficient
        * config.solar_area_m2
        / config.mass_kg
    )
    return scale(magnitude, _unit(config.sun_direction_inertial))


IlluminationModel = Callable[[OrbitState], bool]


def combined_acceleration(
    state: OrbitState,
    config: PerturbationConfig,
    illumination_model: IlluminationModel | None = None,
) -> Vector3:
    config.validate()
    illuminated = True if illumination_model is None else bool(illumination_model(state))
    return add(
        add(two_body_acceleration(state.position_m, config.mu_m3_s2), j2_acceleration(state.position_m, config)),
        add(
            drag_acceleration(state, config),
            solar_radiation_pressure_acceleration(state, config, illuminated=illuminated),
        ),
    )


def rk4_perturbed_step(
    state: OrbitState,
    dt_s: float,
    config: PerturbationConfig,
    illumination_model: IlluminationModel | None = None,
) -> OrbitState:
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")

    def derivative(position: Vector3, velocity: Vector3, epoch: float) -> tuple[Vector3, Vector3]:
        local = OrbitState(position, velocity, epoch)
        return velocity, combined_acceleration(local, config, illumination_model)

    p0, v0, t0 = state.position_m, state.velocity_m_s, state.epoch_s
    k1p, k1v = derivative(p0, v0, t0)
    k2p, k2v = derivative(
        add(p0, scale(0.5 * dt_s, k1p)),
        add(v0, scale(0.5 * dt_s, k1v)),
        t0 + 0.5 * dt_s,
    )
    k3p, k3v = derivative(
        add(p0, scale(0.5 * dt_s, k2p)),
        add(v0, scale(0.5 * dt_s, k2v)),
        t0 + 0.5 * dt_s,
    )
    k4p, k4v = derivative(
        add(p0, scale(dt_s, k3p)),
        add(v0, scale(dt_s, k3v)),
        t0 + dt_s,
    )
    next_position = add(
        p0,
        scale(dt_s / 6.0, add(add(k1p, scale(2.0, k2p)), add(scale(2.0, k3p), k4p))),
    )
    next_velocity = add(
        v0,
        scale(dt_s / 6.0, add(add(k1v, scale(2.0, k2v)), add(scale(2.0, k3v), k4v))),
    )
    require_finite((*next_position, *next_velocity), "perturbed orbit")
    return OrbitState(next_position, next_velocity, t0 + dt_s)


def propagate_perturbed(
    initial_state: OrbitState,
    duration_s: float,
    step_s: float,
    config: PerturbationConfig,
    illumination_model: IlluminationModel | None = None,
) -> tuple[OrbitState, ...]:
    if duration_s <= 0.0 or step_s <= 0.0:
        raise ValueError("duration_s and step_s must be positive")
    states = [initial_state]
    state = initial_state
    remaining = duration_s
    while remaining > 1e-12:
        dt = min(step_s, remaining)
        state = rk4_perturbed_step(state, dt, config, illumination_model)
        states.append(state)
        remaining -= dt
    return tuple(states)


def keplerian_to_cartesian(
    semimajor_axis_m: float,
    eccentricity: float,
    inclination_rad: float,
    raan_rad: float,
    argument_of_periapsis_rad: float,
    true_anomaly_rad: float,
    mu_m3_s2: float,
    epoch_s: float = 0.0,
) -> OrbitState:
    if semimajor_axis_m <= 0.0 or mu_m3_s2 <= 0.0:
        raise ValueError("semimajor axis and mu must be positive")
    if not 0.0 <= eccentricity < 1.0:
        raise ValueError("only bound elliptic orbits with 0 <= e < 1 are supported")
    parameter = semimajor_axis_m * (1.0 - eccentricity**2)
    radius = parameter / (1.0 + eccentricity * cos(true_anomaly_rad))
    perifocal_position = (radius * cos(true_anomaly_rad), radius * sin(true_anomaly_rad), 0.0)
    speed_factor = sqrt(mu_m3_s2 / parameter)
    perifocal_velocity = (
        -speed_factor * sin(true_anomaly_rad),
        speed_factor * (eccentricity + cos(true_anomaly_rad)),
        0.0,
    )

    cos_o, sin_o = cos(raan_rad), sin(raan_rad)
    cos_i, sin_i = cos(inclination_rad), sin(inclination_rad)
    cos_w, sin_w = cos(argument_of_periapsis_rad), sin(argument_of_periapsis_rad)
    rotation = (
        (
            cos_o * cos_w - sin_o * sin_w * cos_i,
            -cos_o * sin_w - sin_o * cos_w * cos_i,
            sin_o * sin_i,
        ),
        (
            sin_o * cos_w + cos_o * sin_w * cos_i,
            -sin_o * sin_w + cos_o * cos_w * cos_i,
            -cos_o * sin_i,
        ),
        (sin_w * sin_i, cos_w * sin_i, cos_i),
    )

    def transform(vector: Vector3) -> Vector3:
        return tuple(sum(rotation[row][column] * vector[column] for column in range(3)) for row in range(3))  # type: ignore[return-value]

    return OrbitState(transform(perifocal_position), transform(perifocal_velocity), epoch_s)


def osculating_elements(state: OrbitState, mu_m3_s2: float) -> OsculatingElements:
    position = state.position_m
    velocity = state.velocity_m_s
    radius = norm(position)
    speed2 = dot(velocity, velocity)
    h = cross(position, velocity)
    h_norm = norm(h)
    if radius <= 0.0 or h_norm <= 0.0:
        raise ValueError("degenerate orbit state")
    node = cross((0.0, 0.0, 1.0), h)
    node_norm = norm(node)
    eccentricity_vector = subtract(scale((speed2 - mu_m3_s2 / radius) / mu_m3_s2, position), scale(dot(position, velocity) / mu_m3_s2, velocity))
    eccentricity = norm(eccentricity_vector)
    specific_energy = 0.5 * speed2 - mu_m3_s2 / radius
    semimajor_axis = -mu_m3_s2 / (2.0 * specific_energy)
    inclination = acos(max(-1.0, min(1.0, h[2] / h_norm)))
    raan = 0.0 if node_norm <= 1e-15 else atan2(node[1], node[0]) % (2.0 * pi)

    if eccentricity <= 1e-12 or node_norm <= 1e-15:
        argument_of_periapsis = 0.0
    else:
        argument_of_periapsis = atan2(
            dot(cross(node, eccentricity_vector), h) / (node_norm * eccentricity * h_norm),
            dot(node, eccentricity_vector) / (node_norm * eccentricity),
        ) % (2.0 * pi)

    if eccentricity > 1e-12:
        true_anomaly = atan2(
            dot(cross(eccentricity_vector, position), h) / (eccentricity * radius * h_norm),
            dot(eccentricity_vector, position) / (eccentricity * radius),
        ) % (2.0 * pi)
    elif node_norm > 1e-15:
        true_anomaly = atan2(
            dot(cross(node, position), h) / (node_norm * radius * h_norm),
            dot(node, position) / (node_norm * radius),
        ) % (2.0 * pi)
    else:
        true_anomaly = atan2(position[1], position[0]) % (2.0 * pi)

    return OsculatingElements(
        semimajor_axis,
        eccentricity,
        inclination,
        raan,
        argument_of_periapsis,
        true_anomaly,
    )


def unwrap_angle_delta(final_rad: float, initial_rad: float) -> float:
    return (final_rad - initial_rad + pi) % (2.0 * pi) - pi


def j2_secular_raan_rate_rad_s(
    semimajor_axis_m: float,
    eccentricity: float,
    inclination_rad: float,
    config: PerturbationConfig,
) -> float:
    if config.j2 == 0.0:
        return 0.0
    mean_motion = sqrt(config.mu_m3_s2 / semimajor_axis_m**3)
    parameter = semimajor_axis_m * (1.0 - eccentricity**2)
    return -1.5 * config.j2 * mean_motion * (config.body_radius_m / parameter) ** 2 * cos(inclination_rad)


def rms_position_difference(a: Iterable[OrbitState], b: Iterable[OrbitState]) -> float:
    pairs = list(zip(a, b))
    if not pairs:
        raise ValueError("state sequences cannot be empty")
    return sqrt(sum(norm(subtract(left.position_m, right.position_m)) ** 2 for left, right in pairs) / len(pairs))
