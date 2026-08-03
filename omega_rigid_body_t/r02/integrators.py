"""Adaptive forced integration and invariant-preserving torque-free integration."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from .linalg import Quaternion, Vector3, add, max_abs, qderivative_body_to_inertial, qnormalize, qrotate, solve3, sub, vector3
from .model import (
    BalanceReport,
    PrincipalMoments,
    TorqueFunction,
    effective_torque,
    euler_rhs,
    inertial_angular_momentum,
    invariants,
    work_rate,
)


@dataclass(frozen=True)
class Trajectory:
    times: tuple[float, ...]
    omegas: tuple[Vector3, ...]
    quaternions: tuple[Quaternion, ...]
    energies: tuple[float, ...]
    angular_momentum_squared: tuple[float, ...]
    accumulated_work: tuple[float, ...]
    accumulated_angular_impulse_inertial: tuple[Vector3, ...]
    accepted_steps: int
    rejected_steps: int
    balance: BalanceReport

    def to_dict(self, *, include_samples: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "accepted_steps": self.accepted_steps,
            "rejected_steps": self.rejected_steps,
            "sample_count": len(self.times),
            "balance": self.balance.to_dict(),
            "max_energy_drift": max(abs(value - self.energies[0]) for value in self.energies),
            "max_momentum_squared_drift": max(
                abs(value - self.angular_momentum_squared[0]) for value in self.angular_momentum_squared
            ),
        }
        if include_samples:
            data["samples"] = [
                {
                    "time": self.times[index],
                    "omega": list(self.omegas[index]),
                    "quaternion": list(self.quaternions[index]),
                    "energy": self.energies[index],
                    "angular_momentum_squared": self.angular_momentum_squared[index],
                    "accumulated_work": self.accumulated_work[index],
                    "accumulated_angular_impulse_inertial": list(
                        self.accumulated_angular_impulse_inertial[index]
                    ),
                }
                for index in range(len(self.times))
            ]
        return data


@dataclass(frozen=True)
class MidpointTrajectory:
    times: tuple[float, ...]
    omegas: tuple[Vector3, ...]
    iterations: tuple[int, ...]
    max_energy_residual: float
    max_momentum_squared_residual: float

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": len(self.times) - 1,
            "max_newton_iterations": max(self.iterations, default=0),
            "max_energy_residual": self.max_energy_residual,
            "max_momentum_squared_residual": self.max_momentum_squared_residual,
            "samples": [
                {"time": time, "omega": list(omega)}
                for time, omega in zip(self.times, self.omegas)
            ],
        }


def _state_rhs(
    model: PrincipalMoments,
    torque: TorqueFunction | None,
    damping: float,
    time: float,
    state: Sequence[float],
) -> tuple[float, ...]:
    omega = vector3(state[0:3])
    q = qnormalize(state[3:7])
    tau = effective_torque(time, omega, q, torque, damping)
    omega_dot = euler_rhs(model, omega, tau)
    q_dot = qderivative_body_to_inertial(q, omega)
    work_dot = work_rate(tau, omega)
    impulse_dot = qrotate(q, tau)
    return (*omega_dot, *q_dot, work_dot, *impulse_dot)


def _combine(base: Sequence[float], dt: float, terms: Sequence[tuple[float, Sequence[float]]]) -> tuple[float, ...]:
    return tuple(
        base[index] + dt * sum(coefficient * vector[index] for coefficient, vector in terms)
        for index in range(len(base))
    )


def _dormand_prince_step(rhs, time: float, state: tuple[float, ...], dt: float):
    k1 = rhs(time, state)
    k2 = rhs(time + dt / 5.0, _combine(state, dt, ((1.0 / 5.0, k1),)))
    k3 = rhs(time + 3.0 * dt / 10.0, _combine(state, dt, ((3.0 / 40.0, k1), (9.0 / 40.0, k2))))
    k4 = rhs(
        time + 4.0 * dt / 5.0,
        _combine(state, dt, ((44.0 / 45.0, k1), (-56.0 / 15.0, k2), (32.0 / 9.0, k3))),
    )
    k5 = rhs(
        time + 8.0 * dt / 9.0,
        _combine(
            state,
            dt,
            (
                (19372.0 / 6561.0, k1),
                (-25360.0 / 2187.0, k2),
                (64448.0 / 6561.0, k3),
                (-212.0 / 729.0, k4),
            ),
        ),
    )
    k6 = rhs(
        time + dt,
        _combine(
            state,
            dt,
            (
                (9017.0 / 3168.0, k1),
                (-355.0 / 33.0, k2),
                (46732.0 / 5247.0, k3),
                (49.0 / 176.0, k4),
                (-5103.0 / 18656.0, k5),
            ),
        ),
    )
    fifth = _combine(
        state,
        dt,
        (
            (35.0 / 384.0, k1),
            (500.0 / 1113.0, k3),
            (125.0 / 192.0, k4),
            (-2187.0 / 6784.0, k5),
            (11.0 / 84.0, k6),
        ),
    )
    k7 = rhs(time + dt, fifth)
    fourth = _combine(
        state,
        dt,
        (
            (5179.0 / 57600.0, k1),
            (7571.0 / 16695.0, k3),
            (393.0 / 640.0, k4),
            (-92097.0 / 339200.0, k5),
            (187.0 / 2100.0, k6),
            (1.0 / 40.0, k7),
        ),
    )
    error = tuple(fifth[index] - fourth[index] for index in range(len(state)))
    return fifth, error


def simulate_adaptive(
    model: PrincipalMoments,
    omega0: Sequence[float],
    *,
    t_end: float,
    samples: int = 256,
    quaternion0: Sequence[float] = (1.0, 0.0, 0.0, 0.0),
    torque: TorqueFunction | None = None,
    damping: float = 0.0,
    rtol: float = 1e-10,
    atol: float = 1e-12,
    initial_step: float | None = None,
    max_steps: int = 2_000_000,
) -> Trajectory:
    if not isfinite(t_end) or t_end < 0.0:
        raise ValueError("t_end must be finite and non-negative")
    if samples < 1:
        raise ValueError("samples must be at least 1")
    if rtol <= 0.0 or atol <= 0.0:
        raise ValueError("rtol and atol must be positive")
    omega_initial = vector3(omega0)
    q_initial = qnormalize(quaternion0)
    state: tuple[float, ...] = (*omega_initial, *q_initial, 0.0, 0.0, 0.0, 0.0)
    rhs = lambda time, value: _state_rhs(model, torque, damping, time, value)
    targets = tuple(t_end * index / samples for index in range(samples + 1))
    time = 0.0
    step = initial_step if initial_step is not None else max(1e-8, t_end / max(1000, samples * 4))
    if step <= 0.0 or not isfinite(step):
        raise ValueError("initial_step must be finite and positive")
    accepted = 0
    rejected = 0
    output_states: list[tuple[float, ...]] = [state]

    for target in targets[1:]:
        while time < target:
            if accepted + rejected >= max_steps:
                raise RuntimeError("adaptive integrator exceeded max_steps")
            dt = min(step, target - time)
            candidate, error = _dormand_prince_step(rhs, time, state, dt)
            scales = tuple(atol + rtol * max(abs(state[i]), abs(candidate[i])) for i in range(len(state)))
            error_norm = max(abs(error[i]) / scales[i] for i in range(len(state)))
            if error_norm <= 1.0:
                time += dt
                normalized_q = qnormalize(candidate[3:7])
                state = (*candidate[0:3], *normalized_q, *candidate[7:])
                accepted += 1
                factor = 5.0 if error_norm == 0.0 else min(5.0, max(0.2, 0.9 * error_norm ** (-0.2)))
                step = dt * factor
            else:
                rejected += 1
                factor = max(0.1, 0.9 * error_norm ** (-0.25))
                step = dt * factor
        output_states.append(state)

    omegas = tuple(vector3(value[0:3]) for value in output_states)
    quaternions = tuple(qnormalize(value[3:7]) for value in output_states)
    inv = tuple(invariants(model, omega) for omega in omegas)
    works = tuple(value[7] for value in output_states)
    impulses = tuple(vector3(value[8:11]) for value in output_states)
    initial_l = inertial_angular_momentum(model, omegas[0], quaternions[0])
    final_l = inertial_angular_momentum(model, omegas[-1], quaternions[-1])
    delta_l = sub(final_l, initial_l)
    impulse_residual = sub(delta_l, impulses[-1])
    energy_change = inv[-1].energy - inv[0].energy
    balance = BalanceReport(
        energy_change=energy_change,
        accumulated_work=works[-1],
        energy_balance_residual=energy_change - works[-1],
        angular_momentum_change_inertial=delta_l,
        accumulated_angular_impulse_inertial=impulses[-1],
        angular_impulse_balance_residual=impulse_residual,
    )
    return Trajectory(
        times=targets,
        omegas=omegas,
        quaternions=quaternions,
        energies=tuple(value.energy for value in inv),
        angular_momentum_squared=tuple(value.angular_momentum_squared for value in inv),
        accumulated_work=works,
        accumulated_angular_impulse_inertial=impulses,
        accepted_steps=accepted,
        rejected_steps=rejected,
        balance=balance,
    )


def _midpoint_residual_and_jacobian(
    model: PrincipalMoments,
    previous: Vector3,
    candidate: Vector3,
    dt: float,
):
    midpoint = tuple(0.5 * (previous[i] + candidate[i]) for i in range(3))
    w1, w2, w3 = midpoint
    a1 = (model.i2 - model.i3) / model.i1
    a2 = (model.i3 - model.i1) / model.i2
    a3 = (model.i1 - model.i2) / model.i3
    rhs = (a1 * w2 * w3, a2 * w3 * w1, a3 * w1 * w2)
    residual = tuple(candidate[i] - previous[i] - dt * rhs[i] for i in range(3))
    jacobian = (
        (1.0, -0.5 * dt * a1 * w3, -0.5 * dt * a1 * w2),
        (-0.5 * dt * a2 * w3, 1.0, -0.5 * dt * a2 * w1),
        (-0.5 * dt * a3 * w2, -0.5 * dt * a3 * w1, 1.0),
    )
    return residual, jacobian


def midpoint_step(
    model: PrincipalMoments,
    omega: Sequence[float],
    dt: float,
    *,
    tolerance: float = 1e-13,
    max_iterations: int = 20,
) -> tuple[Vector3, int]:
    if dt <= 0.0 or not isfinite(dt):
        raise ValueError("dt must be finite and positive")
    previous = vector3(omega)
    explicit = euler_rhs(model, previous)
    candidate = tuple(previous[i] + dt * explicit[i] for i in range(3))
    for iteration in range(1, max_iterations + 1):
        residual, jacobian = _midpoint_residual_and_jacobian(model, previous, candidate, dt)
        if max_abs(residual) <= tolerance * max(1.0, max_abs(candidate)):
            return candidate, iteration
        correction = solve3(jacobian, tuple(-value for value in residual))
        candidate = add(candidate, correction)
    raise ArithmeticError("implicit midpoint Newton solve did not converge")


def integrate_midpoint_torque_free(
    model: PrincipalMoments,
    omega0: Sequence[float],
    *,
    t_end: float,
    steps: int,
    tolerance: float = 1e-13,
) -> MidpointTrajectory:
    if t_end < 0.0 or not isfinite(t_end):
        raise ValueError("t_end must be finite and non-negative")
    if steps < 1:
        raise ValueError("steps must be at least 1")
    dt = t_end / steps
    state = vector3(omega0)
    reference = invariants(model, state)
    times = [0.0]
    states = [state]
    iterations: list[int] = []
    max_energy = 0.0
    max_momentum = 0.0
    for index in range(steps):
        state, count = midpoint_step(model, state, dt, tolerance=tolerance)
        observed = invariants(model, state)
        max_energy = max(max_energy, abs(observed.energy - reference.energy))
        max_momentum = max(max_momentum, abs(observed.angular_momentum_squared - reference.angular_momentum_squared))
        times.append((index + 1) * dt)
        states.append(state)
        iterations.append(count)
    return MidpointTrajectory(
        times=tuple(times),
        omegas=tuple(states),
        iterations=tuple(iterations),
        max_energy_residual=max_energy,
        max_momentum_squared_residual=max_momentum,
    )
