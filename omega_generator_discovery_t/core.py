"""Unified OAK-safe generator-discovery primitives.

The module implements small, dependency-free reference algorithms.  It is not a
claim that every physical process is identifiable from finite observations.
Every result carries residuals and an epistemic status.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, log
from typing import Iterable, Mapping, Sequence, TypeAlias

Vector: TypeAlias = tuple[float, ...]
Matrix: TypeAlias = tuple[tuple[float, ...], ...]

_EPS = 1.0e-12


def _vector(values: Iterable[float]) -> Vector:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError("A vector cannot be empty")
    if not all(isfinite(value) for value in result):
        raise ValueError("Vector entries must be finite")
    return result


def matrix(rows: Iterable[Iterable[float]]) -> Matrix:
    result = tuple(_vector(row) for row in rows)
    if not result:
        raise ValueError("A matrix cannot be empty")
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise ValueError("Matrix rows must share one width")
    return result


def shape(value: Matrix) -> tuple[int, int]:
    return len(value), len(value[0])


def transpose(value: Matrix) -> Matrix:
    rows, columns = shape(value)
    return tuple(tuple(value[row][column] for row in range(rows)) for column in range(columns))


def multiply(left: Matrix, right: Matrix) -> Matrix:
    lr, lc = shape(left)
    rr, rc = shape(right)
    if lc != rr:
        raise ValueError(f"Incompatible shapes {lr}x{lc} and {rr}x{rc}")
    right_t = transpose(right)
    return tuple(
        tuple(sum(a*b for a, b in zip(row, column)) for column in right_t)
        for row in left
    )


def identity(size: int) -> Matrix:
    if size <= 0:
        raise ValueError("Identity size must be positive")
    return tuple(tuple(1.0 if i == j else 0.0 for j in range(size)) for i in range(size))


def subtract(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("Shapes must match")
    return tuple(tuple(a-b for a, b in zip(lrow, rrow)) for lrow, rrow in zip(left, right))


def frobenius_norm(value: Matrix) -> float:
    return sum(entry*entry for row in value for entry in row) ** 0.5


def relative_matrix_error(target: Matrix, estimate: Matrix) -> float:
    return frobenius_norm(subtract(target, estimate)) / max(frobenius_norm(target), _EPS)


def apply_matrix(value: Matrix, vector: Sequence[float]) -> Vector:
    vec = _vector(vector)
    if len(vec) != shape(value)[1]:
        raise ValueError("Vector dimension does not match matrix")
    return tuple(sum(a*b for a, b in zip(row, vec)) for row in value)


def commutator(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right) or shape(left)[0] != shape(left)[1]:
        raise ValueError("Commutator operands must have the same square shape")
    return subtract(multiply(left, right), multiply(right, left))


@dataclass(frozen=True, slots=True)
class AffineGenerator1D:
    """Recovered map ``y = scale*x + translation``.

    ``log_scale`` is the coefficient of ``x d/dx`` when ``scale > 0``.
    A negative scale is kept as a discrete reflection sector.
    """

    scale: float
    translation: float
    log_scale: float | None
    discrete_sector: str
    relative_residual: float
    status: str = "identified_from_pairs_not_causal"

    def transform(self, x: float) -> float:
        return self.scale * float(x) + self.translation

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def identify_affine_1d(source: Sequence[float], target: Sequence[float]) -> AffineGenerator1D:
    x = _vector(source)
    y = _vector(target)
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Source and target need the same length >= 2")
    mean_x = sum(x)/len(x)
    mean_y = sum(y)/len(y)
    variance = sum((value-mean_x)**2 for value in x)
    if variance <= _EPS:
        raise ValueError("Source samples must vary")
    covariance = sum((a-mean_x)*(b-mean_y) for a, b in zip(x, y))
    scale = covariance/variance
    translation = mean_y-scale*mean_x
    predicted = tuple(scale*value+translation for value in x)
    denominator = max(sum(value*value for value in y) ** 0.5, _EPS)
    residual = sum((a-b)**2 for a, b in zip(y, predicted)) ** 0.5 / denominator
    if scale > _EPS:
        sector = "orientation_preserving"
        log_scale = log(scale)
    elif scale < -_EPS:
        sector = "reflection_times_positive_scale"
        log_scale = log(abs(scale))
    else:
        sector = "singular_collapse"
        log_scale = None
    return AffineGenerator1D(scale, translation, log_scale, sector, residual)


@dataclass(frozen=True, slots=True)
class LinearGeneratorOperator:
    """Discrete affine state operator fitted from a scalar trajectory."""

    multiplier: float
    forcing: float
    step: float
    continuous_rate: float | None
    residual: float
    status: str = "local_scalar_generator_candidate"

    def predict(self, state: float, steps: int = 1) -> float:
        if steps < 0:
            raise ValueError("steps must be non-negative")
        value = float(state)
        for _ in range(steps):
            value = self.multiplier * value + self.forcing
        return value


def fit_scalar_generator(states: Sequence[float], step: float = 1.0) -> LinearGeneratorOperator:
    if step <= 0:
        raise ValueError("step must be positive")
    values = _vector(states)
    if len(values) < 3:
        raise ValueError("At least three states are required")
    fit = identify_affine_1d(values[:-1], values[1:])
    rate = log(fit.scale)/step if fit.scale > _EPS else None
    return LinearGeneratorOperator(fit.scale, fit.translation, step, rate, fit.relative_residual)


def semigroup_defect(one_step: Matrix, two_step: Matrix) -> float:
    if shape(one_step)[0] != shape(one_step)[1]:
        raise ValueError("One-step operator must be square")
    return relative_matrix_error(two_step, multiply(one_step, one_step))


@dataclass(frozen=True, slots=True)
class OrderExperiment:
    ab: Matrix
    ba: Matrix
    normalized_order_effect: float
    commutator_norm: float
    status: str = "order_sensitivity_not_causality"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def design_order_experiment(a: Matrix, b: Matrix) -> OrderExperiment:
    ab = multiply(a, b)
    ba = multiply(b, a)
    effect = frobenius_norm(subtract(ab, ba)) / max(frobenius_norm(ab), frobenius_norm(ba), _EPS)
    return OrderExperiment(ab, ba, effect, frobenius_norm(commutator(a, b)))


@dataclass(frozen=True, slots=True)
class GeneratorSyndrome:
    expected: Matrix
    observed: Matrix
    residual: Matrix
    normalized_magnitude: float
    classification: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def generator_syndrome(expected: Matrix, observed: Matrix, *, drift_threshold: float = 0.05) -> GeneratorSyndrome:
    if shape(expected) != shape(observed):
        raise ValueError("Expected and observed operators must share a shape")
    residual = subtract(observed, expected)
    magnitude = frobenius_norm(residual)/max(frobenius_norm(expected), _EPS)
    if magnitude <= _EPS:
        classification = "nominal"
    elif magnitude <= drift_threshold:
        classification = "continuous_drift_candidate"
    else:
        classification = "event_or_model_failure_candidate"
    return GeneratorSyndrome(expected, observed, residual, magnitude, classification)


@dataclass(frozen=True, slots=True)
class MorphIR:
    name: str
    domain: str
    codomain: str
    continuous_generators: tuple[str, ...]
    discrete_events: tuple[str, ...]
    singular_events: tuple[str, ...]
    invariants: tuple[str, ...]
    residual: float
    uncertainty: float
    status: str = "compiled_candidate"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compile_morph_ir(specification: Mapping[str, object]) -> MorphIR:
    def names(key: str) -> tuple[str, ...]:
        raw = specification.get(key, ())
        if isinstance(raw, str):
            return (raw,)
        if not isinstance(raw, Sequence):
            raise ValueError(f"{key} must be a sequence")
        return tuple(str(item) for item in raw)

    name = str(specification.get("name", "unnamed_morphism"))
    domain = str(specification.get("domain", "unknown"))
    codomain = str(specification.get("codomain", "unknown"))
    residual = float(specification.get("residual", 0.0))
    uncertainty = float(specification.get("uncertainty", 0.0))
    if residual < 0 or uncertainty < 0:
        raise ValueError("Residual and uncertainty must be non-negative")
    return MorphIR(
        name=name,
        domain=domain,
        codomain=codomain,
        continuous_generators=names("continuous_generators"),
        discrete_events=names("discrete_events"),
        singular_events=names("singular_events"),
        invariants=names("invariants"),
        residual=residual,
        uncertainty=uncertainty,
    )
