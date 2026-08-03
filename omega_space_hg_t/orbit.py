"""Deterministic two-body orbital mechanics for Ω-SPACE-HG-T∞ R0.1.

This is a transparent educational/research baseline. It is not a replacement
for validated high-fidelity tools such as GMAT, Orekit or operational flight
dynamics systems.
"""
from __future__ import annotations

from math import pi, sqrt
from typing import Iterable

from .models import OrbitState, Vector3, require_finite


def add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(value: float, vector: Vector3) -> Vector3:
    return (value * vector[0], value * vector[1], value * vector[2])


def dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(vector: Vector3) -> float:
    return sqrt(dot(vector, vector))


def two_body_acceleration(position_m: Vector3, mu_m3_s2: float) -> Vector3:
    radius = norm(position_m)
    if radius <= 0.0:
        raise ValueError("position radius must be positive")
    return scale(-mu_m3_s2 / radius**3, position_m)


def specific_energy(state: OrbitState, mu_m3_s2: float) -> float:
    return 0.5 * dot(state.velocity_m_s, state.velocity_m_s) - mu_m3_s2 / norm(state.position_m)


def specific_angular_momentum(state: OrbitState) -> Vector3:
    return cross(state.position_m, state.velocity_m_s)


def semimajor_axis_m(state: OrbitState, mu_m3_s2: float) -> float:
    energy = specific_energy(state, mu_m3_s2)
    if energy >= 0.0:
        raise ValueError("state is not on a bound two-body orbit")
    return -mu_m3_s2 / (2.0 * energy)


def orbital_period_s(state: OrbitState, mu_m3_s2: float) -> float:
    semimajor_axis = semimajor_axis_m(state, mu_m3_s2)
    return 2.0 * pi * sqrt(semimajor_axis**3 / mu_m3_s2)


def circular_orbit_state(radius_m: float, mu_m3_s2: float, epoch_s: float = 0.0) -> OrbitState:
    if radius_m <= 0.0 or mu_m3_s2 <= 0.0:
        raise ValueError("radius and gravitational parameter must be positive")
    speed = sqrt(mu_m3_s2 / radius_m)
    return OrbitState((radius_m, 0.0, 0.0), (0.0, speed, 0.0), epoch_s)


def velocity_verlet_step(state: OrbitState, dt_s: float, mu_m3_s2: float) -> OrbitState:
    """Advance one symplectic velocity-Verlet step."""

    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    acceleration_0 = two_body_acceleration(state.position_m, mu_m3_s2)
    next_position = add(
        add(state.position_m, scale(dt_s, state.velocity_m_s)),
        scale(0.5 * dt_s * dt_s, acceleration_0),
    )
    acceleration_1 = two_body_acceleration(next_position, mu_m3_s2)
    next_velocity = add(
        state.velocity_m_s,
        scale(0.5 * dt_s, add(acceleration_0, acceleration_1)),
    )
    require_finite((*next_position, *next_velocity), "propagated orbit")
    return OrbitState(next_position, next_velocity, state.epoch_s + dt_s)


def propagate_two_body(
    initial_state: OrbitState,
    duration_s: float,
    step_s: float,
    mu_m3_s2: float,
) -> tuple[OrbitState, ...]:
    if duration_s <= 0.0 or step_s <= 0.0:
        raise ValueError("duration_s and step_s must be positive")
    states = [initial_state]
    state = initial_state
    remaining = duration_s
    while remaining > 1e-12:
        dt = min(step_s, remaining)
        state = velocity_verlet_step(state, dt, mu_m3_s2)
        states.append(state)
        remaining -= dt
    return tuple(states)


def relative_energy_drift(states: Iterable[OrbitState], mu_m3_s2: float) -> float:
    energies = [specific_energy(state, mu_m3_s2) for state in states]
    if not energies:
        raise ValueError("states cannot be empty")
    reference = max(abs(energies[0]), 1e-30)
    return max(abs(value - energies[0]) for value in energies) / reference
