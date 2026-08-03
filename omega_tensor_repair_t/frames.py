"""Analysis/synthesis frames for redundant tensor channel systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .linalg import Matrix, Vector, add, flatten, frobenius_norm, subtract, unflatten, zeros

Analyzer = Callable[[Matrix], Vector]
Synthesizer = Callable[[Vector], Matrix]


@dataclass(frozen=True)
class FrameChannel:
    name: str
    analyze: Analyzer
    synthesize: Synthesizer
    dimension: int
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.dimension < 0:
            raise ValueError("dimension must be non-negative")
        if self.weight <= 0.0:
            raise ValueError("weight must be positive")


@dataclass(frozen=True)
class FrameResult:
    coefficients: dict[str, Vector]
    reconstruction: Matrix
    residual: Matrix
    energy_ratio: float


class TensorFrame:
    """Finite analysis/synthesis bundle allowing exact or redundant channels."""

    def __init__(self, rows: int, cols: int, channels: Iterable[FrameChannel]):
        if rows <= 0 or cols <= 0:
            raise ValueError("frame shape must be positive")
        self.rows = rows
        self.cols = cols
        self.channels = tuple(channels)
        names = [channel.name for channel in self.channels]
        if len(names) != len(set(names)):
            raise ValueError("frame channel names must be unique")

    def analyze(self, tensor: Matrix) -> dict[str, Vector]:
        if len(tensor) != self.rows or any(len(row) != self.cols for row in tensor):
            raise ValueError("tensor shape does not match frame")
        coefficients: dict[str, Vector] = {}
        for channel in self.channels:
            values = tuple(float(value) for value in channel.analyze(tensor))
            if len(values) != channel.dimension:
                raise ValueError(f"channel {channel.name!r} returned the wrong dimension")
            coefficients[channel.name] = values
        return coefficients

    def synthesize(self, coefficients: dict[str, Sequence[float]]) -> Matrix:
        result = zeros(self.rows, self.cols)
        for channel in self.channels:
            if channel.name not in coefficients:
                continue
            values = tuple(float(value) for value in coefficients[channel.name])
            if len(values) != channel.dimension:
                raise ValueError(f"channel {channel.name!r} has the wrong dimension")
            result = add(result, channel.synthesize(values))
        return result

    def round_trip(self, tensor: Matrix) -> FrameResult:
        coefficients = self.analyze(tensor)
        reconstruction = self.synthesize(coefficients)
        residual = subtract(tensor, reconstruction)
        input_energy = frobenius_norm(tensor) ** 2
        coefficient_energy = sum(
            channel.weight * sum(value * value for value in coefficients[channel.name])
            for channel in self.channels
        )
        ratio = coefficient_energy / input_energy if input_energy else 1.0
        return FrameResult(coefficients, reconstruction, residual, ratio)


def identity_frame(rows: int, cols: int) -> TensorFrame:
    size = rows * cols
    return TensorFrame(
        rows,
        cols,
        (
            FrameChannel(
                name="full",
                dimension=size,
                analyze=flatten,
                synthesize=lambda vector: unflatten(vector, rows, cols),
            ),
        ),
    )
