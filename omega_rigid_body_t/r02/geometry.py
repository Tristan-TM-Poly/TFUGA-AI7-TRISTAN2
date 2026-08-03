"""Poinsot geometry, solid angles and Montgomery phase."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan2, pi
from typing import Iterable, Sequence

from .analytic import ExactParameters, exact_omega
from .integrators import Trajectory, simulate_adaptive
from .linalg import (
    Vector3,
    cross,
    dot,
    norm,
    normalize,
    qrelative,
    qrotate,
    quaternion_axis_error,
    scale,
    signed_quaternion_angle_about_axis,
    sub,
    vector3,
)
from .model import PrincipalMoments


@dataclass(frozen=True)
class PhaseClosureReport:
    period: float
    dynamic_phase: float
    solid_angle: float
    montgomery_phase: float
    quaternion_phase: float
    phase_residual: float
    monodromy_axis_error: float
    closure_error_body_momentum: float
    samples: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def wrap_angle(angle: float) -> float:
    return angle % (2.0 * pi)


def angular_distance_modulo(left: float, right: float) -> float:
    delta = (left - right + pi) % (2.0 * pi) - pi
    return abs(delta)


def body_momentum_direction(model: PrincipalMoments, omega: Sequence[float]) -> Vector3:
    momentum = model.angular_momentum_body(omega)
    return normalize(momentum)  # type: ignore[return-value]


def _reference_for_polygon(points: Sequence[Vector3]) -> Vector3:
    candidates: list[Vector3] = []
    summed = (
        sum(point[0] for point in points),
        sum(point[1] for point in points),
        sum(point[2] for point in points),
    )
    if norm(summed) > 1e-12:
        candidates.append(normalize(summed))  # type: ignore[arg-type]
    candidates.extend(
        [
            (1.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, -1.0),
        ]
    )
    return max(candidates, key=lambda candidate: min(dot(candidate, point) for point in points))


def oriented_solid_angle_closed_polygon(points: Iterable[Sequence[float]]) -> float:
    """Return the oriented solid angle of a closed spherical polygon."""
    normalized_points = [normalize(vector3(point)) for point in points]
    vertices: list[Vector3] = [tuple(point) for point in normalized_points]  # type: ignore[list-item]
    if len(vertices) < 3:
        raise ValueError("at least three spherical vertices are required")
    if norm(sub(vertices[0], vertices[-1])) < 1e-12:
        vertices.pop()
    reference = _reference_for_polygon(vertices)
    total = 0.0
    for left, right in zip(vertices, vertices[1:] + vertices[:1]):
        numerator = dot(reference, cross(left, right))
        denominator = 1.0 + dot(reference, left) + dot(left, right) + dot(right, reference)
        total += 2.0 * atan2(numerator, denominator)
    return total


def momentum_sphere_path(
    model: PrincipalMoments,
    parameters: ExactParameters,
    *,
    samples: int = 4096,
) -> tuple[Vector3, ...]:
    if samples < 64:
        raise ValueError("samples must be at least 64")
    return tuple(
        body_momentum_direction(model, exact_omega(parameters.period * index / samples, parameters))
        for index in range(samples)
    )


def montgomery_phase(
    model: PrincipalMoments,
    parameters: ExactParameters,
    *,
    samples: int = 4096,
) -> tuple[float, float, float]:
    path = momentum_sphere_path(model, parameters, samples=samples)
    solid_angle = oriented_solid_angle_closed_polygon(path)
    inv = parameters.invariants
    dynamic = 2.0 * inv.energy * parameters.period / inv.angular_momentum
    geometric_total = wrap_angle(dynamic - solid_angle)
    return dynamic, solid_angle, geometric_total


def phase_closure_report(
    model: PrincipalMoments,
    parameters: ExactParameters,
    *,
    samples: int = 2048,
    rtol: float = 2e-11,
    atol: float = 2e-13,
) -> PhaseClosureReport:
    if samples < 128:
        raise ValueError("samples must be at least 128")
    dynamic, solid_angle, predicted = montgomery_phase(model, parameters, samples=samples)
    trajectory = simulate_adaptive(
        model,
        exact_omega(0.0, parameters),
        t_end=parameters.period,
        samples=max(128, samples // 8),
        torque=None,
        damping=0.0,
        rtol=rtol,
        atol=atol,
    )
    initial_momentum = model.angular_momentum_body(trajectory.omegas[0])
    inertial_axis = qrotate(trajectory.quaternions[0], initial_momentum)
    relative = qrelative(trajectory.quaternions[-1], trajectory.quaternions[0])
    observed = signed_quaternion_angle_about_axis(relative, inertial_axis)
    axis_error = quaternion_axis_error(relative, inertial_axis)
    final_body_direction = body_momentum_direction(model, trajectory.omegas[-1])
    initial_body_direction = body_momentum_direction(model, trajectory.omegas[0])
    closure = norm(sub(final_body_direction, initial_body_direction))
    return PhaseClosureReport(
        period=parameters.period,
        dynamic_phase=dynamic,
        solid_angle=solid_angle,
        montgomery_phase=predicted,
        quaternion_phase=observed,
        phase_residual=angular_distance_modulo(predicted, observed),
        monodromy_axis_error=axis_error,
        closure_error_body_momentum=closure,
        samples=samples,
    )


def polhode_points(parameters: ExactParameters, *, samples: int = 1024) -> tuple[Vector3, ...]:
    if samples < 4:
        raise ValueError("samples must be at least 4")
    return tuple(exact_omega(parameters.period * index / samples, parameters) for index in range(samples + 1))


def herpolhode_points(model: PrincipalMoments, trajectory: Trajectory) -> tuple[Vector3, ...]:
    """Project inertial angular velocity onto the invariable plane."""
    initial_l = qrotate(trajectory.quaternions[0], model.angular_momentum_body(trajectory.omegas[0]))
    lhat = normalize(initial_l)
    points = []
    for omega, q in zip(trajectory.omegas, trajectory.quaternions):
        omega_inertial = qrotate(q, omega)
        parallel = scale(dot(omega_inertial, lhat), lhat)  # type: ignore[arg-type]
        points.append(sub(omega_inertial, parallel))
    return tuple(points)
