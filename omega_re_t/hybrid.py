"""Low-order hybrid-system identification for synthetic research fixtures."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Iterable, Mapping, Sequence

Vector = tuple[float, ...]


def _dot(row: Sequence[float], vector: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(row, vector))


@dataclass(frozen=True, slots=True)
class AffineDynamics:
    matrix: tuple[tuple[float, ...], ...]
    input_matrix: tuple[tuple[float, ...], ...]
    bias: Vector

    def derivative(self, state: Vector, control: Vector) -> Vector:
        if len(self.matrix) != len(self.bias):
            raise ValueError("matrix row count must match bias")
        if any(len(row) != len(state) for row in self.matrix):
            raise ValueError("state dimension mismatch")
        if len(self.input_matrix) != len(self.bias) or any(len(row) != len(control) for row in self.input_matrix):
            raise ValueError("control dimension mismatch")
        return tuple(
            _dot(self.matrix[index], state) + _dot(self.input_matrix[index], control) + self.bias[index]
            for index in range(len(self.bias))
        )


@dataclass(frozen=True, slots=True)
class Guard:
    variable_index: int
    operator: str
    threshold: float
    target_mode: str

    def fires(self, state: Vector) -> bool:
        value = state[self.variable_index]
        if self.operator == ">=":
            return value >= self.threshold
        if self.operator == ">":
            return value > self.threshold
        if self.operator == "<=":
            return value <= self.threshold
        if self.operator == "<":
            return value < self.threshold
        raise ValueError(f"unsupported guard operator {self.operator!r}")


@dataclass(frozen=True, slots=True)
class HybridMode:
    name: str
    dynamics: AffineDynamics
    guards: tuple[Guard, ...] = ()


@dataclass(frozen=True, slots=True)
class HybridSystem:
    modes: Mapping[str, HybridMode]
    initial_mode: str

    def __post_init__(self) -> None:
        if self.initial_mode not in self.modes:
            raise ValueError("unknown initial mode")
        for mode in self.modes.values():
            for guard in mode.guards:
                if guard.target_mode not in self.modes:
                    raise ValueError("guard targets unknown mode")

    def step(self, mode_name: str, state: Vector, control: Vector, dt: float) -> tuple[str, Vector]:
        if dt <= 0 or not isfinite(dt):
            raise ValueError("dt must be finite and positive")
        mode = self.modes[mode_name]
        derivative = mode.dynamics.derivative(state, control)
        next_state = tuple(value + dt * rate for value, rate in zip(state, derivative))
        next_mode = mode_name
        for guard in mode.guards:
            if guard.fires(next_state):
                next_mode = guard.target_mode
                break
        return next_mode, next_state

    def simulate(
        self,
        initial_state: Vector,
        controls: Sequence[Vector],
        *,
        dt: float,
    ) -> tuple[tuple[str, Vector], ...]:
        mode = self.initial_mode
        state = tuple(float(value) for value in initial_state)
        trace: list[tuple[str, Vector]] = [(mode, state)]
        for control in controls:
            mode, state = self.step(mode, state, tuple(control), dt)
            trace.append((mode, state))
        return tuple(trace)


@dataclass(frozen=True, slots=True)
class HybridObservation:
    mode: str
    state: Vector
    control: Vector
    next_state: Vector
    dt: float


@dataclass(frozen=True, slots=True)
class FitReport:
    mode: str
    coefficients: tuple[tuple[float, ...], ...]
    bias: Vector
    mean_absolute_residual: float
    sample_count: int
    identifiable: bool
    warnings: tuple[str, ...] = ()


def _solve_normal_equations(features: Sequence[Sequence[float]], targets: Sequence[float], ridge: float) -> tuple[float, ...]:
    # Small deterministic Gauss-Jordan solver for synthetic fixtures.
    columns = len(features[0])
    gram = [[0.0 for _ in range(columns)] for _ in range(columns)]
    rhs = [0.0 for _ in range(columns)]
    for row, target in zip(features, targets):
        for i in range(columns):
            rhs[i] += row[i] * target
            for j in range(columns):
                gram[i][j] += row[i] * row[j]
    for i in range(columns):
        gram[i][i] += ridge
    augmented = [gram[i] + [rhs[i]] for i in range(columns)]
    for column in range(columns):
        pivot = max(range(column, columns), key=lambda r: abs(augmented[r][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular design matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(columns):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[column])]
    return tuple(augmented[index][-1] for index in range(columns))


def fit_affine_mode(observations: Iterable[HybridObservation], mode: str, *, ridge: float = 1e-8) -> FitReport:
    rows = [item for item in observations if item.mode == mode]
    if not rows:
        raise ValueError("no observations for requested mode")
    state_dim = len(rows[0].state)
    control_dim = len(rows[0].control)
    if any(len(item.state) != state_dim or len(item.next_state) != state_dim or len(item.control) != control_dim for item in rows):
        raise ValueError("inconsistent dimensions")
    features = [tuple(item.state) + tuple(item.control) + (1.0,) for item in rows]
    coefficients: list[tuple[float, ...]] = []
    residuals: list[float] = []
    for dimension in range(state_dim):
        targets = [(item.next_state[dimension] - item.state[dimension]) / item.dt for item in rows]
        coefficient = _solve_normal_equations(features, targets, ridge)
        coefficients.append(coefficient)
        for feature, target in zip(features, targets):
            residuals.append(abs(_dot(coefficient, feature) - target))
    matrix_and_input = tuple(tuple(row[:-1]) for row in coefficients)
    bias = tuple(row[-1] for row in coefficients)
    identifiable = len(rows) >= state_dim + control_dim + 1
    warnings = () if identifiable else ("Insufficient samples for a fully constrained affine fit.",)
    return FitReport(
        mode=mode,
        coefficients=matrix_and_input,
        bias=bias,
        mean_absolute_residual=sum(residuals) / len(residuals),
        sample_count=len(rows),
        identifiable=identifiable,
        warnings=warnings,
    )
