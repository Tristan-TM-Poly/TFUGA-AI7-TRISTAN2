"""Exact Euler-top branches with arbitrary initial phase/sign recovery."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from typing import Sequence

from ..elliptic import complete_elliptic_k, jacobi_sncndn, near_separatrix_period_asymptotic
from .linalg import Vector3, vector3
from .model import Invariants, PrincipalMoments, invariants


@dataclass(frozen=True)
class ExactParameters:
    regime: str
    invariants: Invariants
    amplitude1: float
    amplitude2: float
    amplitude3: float
    frequency: float
    parameter_m: float
    period: float
    phase: float
    signature: tuple[int, int, int]
    fit_residual: float

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["invariants"] = self.invariants.to_dict()
        data["signature"] = list(self.signature)
        return data


def classify(model: PrincipalMoments, inv: Invariants, *, tolerance: float = 1e-12) -> str:
    if inv.angular_momentum_squared <= 0.0 or inv.energy <= 0.0:
        raise ValueError("energy and angular momentum must be positive")
    lower = inv.angular_momentum_squared / (2.0 * model.i3)
    upper = inv.angular_momentum_squared / (2.0 * model.i1)
    scale = max(1.0, abs(inv.energy), abs(lower), abs(upper))
    if not lower - tolerance * scale <= inv.energy <= upper + tolerance * scale:
        raise ValueError("invariants are outside the torque-free admissible interval")
    threshold = inv.angular_momentum_squared / (2.0 * model.i2)
    if abs(inv.energy - threshold) <= tolerance * max(1.0, abs(threshold)):
        return "separatrix_intermediate_axis"
    return "stable_axis_3" if inv.energy < threshold else "stable_axis_1"


def canonical_parameters(model: PrincipalMoments, inv: Invariants) -> tuple[str, float, float, float, float, float, float]:
    regime = classify(model, inv)
    if regime == "separatrix_intermediate_axis":
        raise ValueError("separatrix uses a hyperbolic branch")
    i1, i2, i3 = model.i1, model.i2, model.i3
    e = inv.energy
    l2 = inv.angular_momentum_squared
    a1 = sqrt(max(0.0, (2.0 * e * i3 - l2) / (i1 * (i3 - i1))))
    a3 = sqrt(max(0.0, (l2 - 2.0 * e * i1) / (i3 * (i3 - i1))))
    if regime == "stable_axis_3":
        a2 = sqrt(max(0.0, (2.0 * e * i3 - l2) / (i2 * (i3 - i2))))
        frequency = sqrt((i3 - i2) * (l2 - 2.0 * e * i1) / (i1 * i2 * i3))
        m = (i2 - i1) * (2.0 * e * i3 - l2) / ((i3 - i2) * (l2 - 2.0 * e * i1))
    else:
        a2 = sqrt(max(0.0, (l2 - 2.0 * e * i1) / (i2 * (i2 - i1))))
        frequency = sqrt((i2 - i1) * (2.0 * e * i3 - l2) / (i1 * i2 * i3))
        m = (i3 - i2) * (l2 - 2.0 * e * i1) / ((i2 - i1) * (2.0 * e * i3 - l2))
    if m < -1e-11 or m > 1.0 + 1e-11:
        raise ArithmeticError(f"derived elliptic parameter outside [0,1]: {m}")
    m = max(0.0, min(1.0, m))
    period = 4.0 * complete_elliptic_k(m) / frequency
    return regime, a1, a2, a3, frequency, m, period


def canonical_omega(u: float, regime: str, amplitudes: tuple[float, float, float], m: float) -> Vector3:
    sn, cn, dn = jacobi_sncndn(u, m)
    a1, a2, a3 = amplitudes
    if regime == "stable_axis_3":
        return (a1 * cn, a2 * sn, a3 * dn)
    if regime == "stable_axis_1":
        return (a1 * dn, a2 * sn, a3 * cn)
    raise ValueError(f"unsupported regime {regime}")


def exact_omega(time: float, parameters: ExactParameters) -> Vector3:
    base = canonical_omega(
        parameters.frequency * float(time) + parameters.phase,
        parameters.regime,
        (parameters.amplitude1, parameters.amplitude2, parameters.amplitude3),
        parameters.parameter_m,
    )
    return tuple(parameters.signature[i] * base[i] for i in range(3))  # type: ignore[return-value]


def exact_parameters_from_state(
    model: PrincipalMoments,
    omega0: Sequence[float],
    *,
    phase_grid: int = 2048,
) -> ExactParameters:
    """Recover the exact real branch from arbitrary non-separatrix initial data."""
    if phase_grid < 128:
        raise ValueError("phase_grid must be at least 128")
    target = vector3(omega0)
    inv = invariants(model, target)
    regime, a1, a2, a3, frequency, m, period = canonical_parameters(model, inv)
    amplitudes = (a1, a2, a3)
    k4 = 4.0 * complete_elliptic_k(m)
    sectors = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))
    scales = tuple(max(abs(target[i]), amplitudes[i], 1e-15) for i in range(3))

    def objective(u: float, signature: tuple[int, int, int]) -> float:
        predicted = canonical_omega(u % k4, regime, amplitudes, m)
        return sum(((signature[i] * predicted[i] - target[i]) / scales[i]) ** 2 for i in range(3))

    best_u = 0.0
    best_signature = sectors[0]
    best_value = float("inf")
    step = k4 / phase_grid
    for signature in sectors:
        for index in range(phase_grid):
            u = index * step
            value = objective(u, signature)
            if value < best_value:
                best_u, best_signature, best_value = u, signature, value

    left = best_u - step
    right = best_u + step
    golden = (sqrt(5.0) - 1.0) / 2.0
    c = right - golden * (right - left)
    d = left + golden * (right - left)
    fc = objective(c, best_signature)
    fd = objective(d, best_signature)
    for _ in range(96):
        if fc <= fd:
            right, d, fd = d, c, fc
            c = right - golden * (right - left)
            fc = objective(c, best_signature)
        else:
            left, c, fc = c, d, fd
            d = left + golden * (right - left)
            fd = objective(d, best_signature)
    phase = (0.5 * (left + right)) % k4
    residual = sqrt(objective(phase, best_signature))
    return ExactParameters(
        regime=regime,
        invariants=inv,
        amplitude1=a1,
        amplitude2=a2,
        amplitude3=a3,
        frequency=frequency,
        parameter_m=m,
        period=period,
        phase=phase,
        signature=best_signature,
        fit_residual=residual,
    )


def separatrix_omega(
    model: PrincipalMoments,
    angular_momentum: float,
    time: float,
    *,
    center_time: float = 0.0,
    signature: tuple[int, int, int] = (1, 1, 1),
) -> Vector3:
    if angular_momentum <= 0.0 or not isfinite(angular_momentum):
        raise ValueError("angular_momentum must be finite and positive")
    if signature[0] * signature[1] * signature[2] != 1:
        raise ValueError("signature must have product +1")
    i1, i2, i3 = model.i1, model.i2, model.i3
    l2 = angular_momentum * angular_momentum
    a1 = sqrt(l2 * (i3 - i2) / (i1 * i2 * (i3 - i1)))
    a2 = angular_momentum / i2
    a3 = sqrt(l2 * (i2 - i1) / (i2 * i3 * (i3 - i1)))
    rate = sqrt(l2 * (i3 - i2) * (i2 - i1) / (i1 * i2 * i2 * i3))
    sn, cn, _ = jacobi_sncndn(rate * (time - center_time), 1.0)
    base = (a1 * cn, a2 * sn, a3 * cn)
    return tuple(signature[i] * base[i] for i in range(3))  # type: ignore[return-value]


def near_separatrix_period(parameters: ExactParameters) -> float:
    return 4.0 * near_separatrix_period_asymptotic(parameters.parameter_m) / parameters.frequency
