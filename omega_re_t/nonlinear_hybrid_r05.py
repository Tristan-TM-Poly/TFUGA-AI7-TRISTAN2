"""Bounded nonlinear hybrid-system identification and simulation primitives."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable, Mapping, Sequence

Vector = tuple[float, ...]


def polynomial_features(state: Sequence[float], degree: int) -> tuple[float, ...]:
    if degree < 1 or degree > 3:
        raise ValueError("degree must be in [1, 3]")
    values = tuple(float(value) for value in state)
    features: list[float] = [1.0]
    features.extend(values)
    if degree >= 2:
        for i, left in enumerate(values):
            for right in values[i:]:
                features.append(left * right)
    if degree >= 3:
        for i, first in enumerate(values):
            for j in range(i, len(values)):
                for k in range(j, len(values)):
                    features.append(first * values[j] * values[k])
    return tuple(features)


def _solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1.0e-12:
            raise ValueError("singular system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [augmented[row][-1] for row in range(n)]


@dataclass(frozen=True)
class PolynomialDynamics:
    output_coefficients: tuple[tuple[float, ...], ...]
    degree: int

    def derivative(self, state: Sequence[float]) -> Vector:
        features = polynomial_features(state, self.degree)
        if any(len(coefficients) != len(features) for coefficients in self.output_coefficients):
            raise ValueError("coefficient dimension mismatch")
        return tuple(
            sum(coefficient * feature for coefficient, feature in zip(coefficients, features, strict=True))
            for coefficients in self.output_coefficients
        )


@dataclass(frozen=True)
class HybridGuard:
    source_mode: str
    target_mode: str
    predicate: Callable[[Vector], bool]
    reset: Callable[[Vector], Vector] | None = None


@dataclass(frozen=True)
class HybridTracePoint:
    step: int
    time: float
    mode: str
    state: Vector


class NonlinearHybridSystem:
    def __init__(
        self,
        *,
        modes: Mapping[str, PolynomialDynamics],
        guards: Iterable[HybridGuard] = (),
    ) -> None:
        if not modes:
            raise ValueError("modes cannot be empty")
        self.modes = dict(modes)
        self.guards = tuple(guards)
        for guard in self.guards:
            if guard.source_mode not in self.modes or guard.target_mode not in self.modes:
                raise ValueError("guard references unknown mode")

    def simulate(
        self,
        *,
        initial_mode: str,
        initial_state: Sequence[float],
        dt: float,
        steps: int,
        state_limit: float = 1.0e9,
    ) -> tuple[HybridTracePoint, ...]:
        if initial_mode not in self.modes:
            raise ValueError("unknown initial mode")
        if dt <= 0.0 or not math.isfinite(dt) or steps < 0:
            raise ValueError("invalid integration budget")
        mode = initial_mode
        state = tuple(float(value) for value in initial_state)
        trace = [HybridTracePoint(0, 0.0, mode, state)]
        for step in range(1, steps + 1):
            derivative = self.modes[mode].derivative(state)
            if len(derivative) != len(state):
                raise ValueError("derivative/state dimension mismatch")
            state = tuple(value + dt * rate for value, rate in zip(state, derivative, strict=True))
            if any(not math.isfinite(value) or abs(value) > state_limit for value in state):
                raise OverflowError("state left bounded simulation envelope")
            for guard in self.guards:
                if guard.source_mode == mode and guard.predicate(state):
                    state = guard.reset(state) if guard.reset else state
                    mode = guard.target_mode
                    break
            trace.append(HybridTracePoint(step, step * dt, mode, state))
        return tuple(trace)


def fit_polynomial_dynamics(
    samples: Iterable[tuple[Sequence[float], Sequence[float]]],
    *,
    degree: int = 2,
    ridge: float = 1.0e-8,
) -> PolynomialDynamics:
    pairs = [(tuple(map(float, state)), tuple(map(float, derivative))) for state, derivative in samples]
    if not pairs:
        raise ValueError("samples cannot be empty")
    state_dim = len(pairs[0][0])
    output_dim = len(pairs[0][1])
    if any(len(state) != state_dim or len(derivative) != output_dim for state, derivative in pairs):
        raise ValueError("sample dimensions must be consistent")
    features = [polynomial_features(state, degree) for state, _ in pairs]
    feature_count = len(features[0])
    if len(pairs) < feature_count:
        raise ValueError("underdetermined polynomial fit")
    gram = [[0.0 for _ in range(feature_count)] for _ in range(feature_count)]
    for row in features:
        for i in range(feature_count):
            for j in range(feature_count):
                gram[i][j] += row[i] * row[j]
    for i in range(feature_count):
        gram[i][i] += ridge
    coefficients: list[tuple[float, ...]] = []
    for output_index in range(output_dim):
        rhs = [0.0 for _ in range(feature_count)]
        for row, (_, derivative) in zip(features, pairs, strict=True):
            for i in range(feature_count):
                rhs[i] += row[i] * derivative[output_index]
        coefficients.append(tuple(_solve_linear(gram, rhs)))
    return PolynomialDynamics(tuple(coefficients), degree)
