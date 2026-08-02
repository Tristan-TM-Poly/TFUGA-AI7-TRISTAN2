from __future__ import annotations

from dataclasses import dataclass
import math
import random
from statistics import fmean, pstdev
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Interval:
    lower: float
    upper: float
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError("Interval lower bound cannot exceed upper bound")
        if self.confidence is not None and not 0 < self.confidence < 1:
            raise ValueError("Interval confidence must be within (0, 1)")

    @property
    def width(self) -> float:
        return self.upper - self.lower

    @property
    def midpoint(self) -> float:
        return 0.5 * (self.lower + self.upper)

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper

    def intersect(self, other: "Interval") -> "Interval | None":
        lower = max(self.lower, other.lower)
        upper = min(self.upper, other.upper)
        if lower > upper:
            return None
        confidence = (
            None
            if self.confidence is None or other.confidence is None
            else min(self.confidence, other.confidence)
        )
        return Interval(lower, upper, confidence)


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    count: int
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float
    quantiles: Mapping[str, float]
    seed: int

    def to_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "mean": self.mean,
            "standard_deviation": self.standard_deviation,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "quantiles": dict(self.quantiles),
            "seed": self.seed,
        }


def quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("Quantile requires at least one value")
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be within [0, 1]")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def monte_carlo(
    model: Callable[[Mapping[str, float]], float],
    samplers: Mapping[str, Callable[[random.Random], float]],
    *,
    samples: int = 10_000,
    seed: int = 0,
) -> DistributionSummary:
    if samples <= 0:
        raise ValueError("Monte Carlo samples must be positive")
    if not samplers:
        raise ValueError("At least one sampler is required")
    rng = random.Random(seed)
    outputs: list[float] = []
    for _ in range(samples):
        parameters = {name: sampler(rng) for name, sampler in samplers.items()}
        output = float(model(parameters))
        if not math.isfinite(output):
            raise ValueError("Model produced a non-finite Monte Carlo output")
        outputs.append(output)
    return DistributionSummary(
        count=samples,
        mean=fmean(outputs),
        standard_deviation=pstdev(outputs),
        minimum=min(outputs),
        maximum=max(outputs),
        quantiles={
            "q01": quantile(outputs, 0.01),
            "q05": quantile(outputs, 0.05),
            "q50": quantile(outputs, 0.50),
            "q95": quantile(outputs, 0.95),
            "q99": quantile(outputs, 0.99),
        },
        seed=seed,
    )


def normal_sampler(mean: float, standard_deviation: float) -> Callable[[random.Random], float]:
    if standard_deviation < 0:
        raise ValueError("Standard deviation cannot be negative")
    return lambda rng: rng.gauss(mean, standard_deviation)


def uniform_sampler(lower: float, upper: float) -> Callable[[random.Random], float]:
    if lower > upper:
        raise ValueError("Uniform lower bound cannot exceed upper bound")
    return lambda rng: rng.uniform(lower, upper)


def triangular_sampler(
    lower: float, mode: float, upper: float
) -> Callable[[random.Random], float]:
    if not lower <= mode <= upper:
        raise ValueError("Triangular parameters must satisfy lower <= mode <= upper")
    return lambda rng: rng.triangular(lower, upper, mode)


def sensitivity_finite_difference(
    model: Callable[[Mapping[str, float]], float],
    point: Mapping[str, float],
    *,
    relative_step: float = 1e-6,
) -> dict[str, float]:
    if relative_step <= 0:
        raise ValueError("Relative step must be positive")
    derivatives: dict[str, float] = {}
    for name, value in point.items():
        step = relative_step * max(1.0, abs(value))
        plus = dict(point)
        minus = dict(point)
        plus[name] = value + step
        minus[name] = value - step
        derivatives[name] = (model(plus) - model(minus)) / (2 * step)
    return derivatives


def combine_independent_standard_uncertainties(
    sensitivities: Mapping[str, float],
    standard_uncertainties: Mapping[str, float],
) -> float:
    if set(sensitivities) != set(standard_uncertainties):
        raise ValueError("Sensitivity and uncertainty parameters must match")
    if any(value < 0 for value in standard_uncertainties.values()):
        raise ValueError("Standard uncertainties cannot be negative")
    return math.sqrt(
        sum(
            (sensitivities[name] * standard_uncertainties[name]) ** 2
            for name in sensitivities
        )
    )
