"""Mixed-radix logical frontier with constant-memory random access."""
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from operator import mul

from .model import VariantAddress

LANGUAGES = ("python", "c", "cpp", "rust")
STRATEGIES = (
    "scalar", "unrolled-2", "unrolled-4", "unrolled-8", "simd-auto", "simd-explicit",
    "blocked-32", "blocked-64", "blocked-256", "streaming", "in-place", "out-of-place",
    "parallel-chunks", "work-stealing", "fused", "cache-aware",
)
PRECISIONS = ("f16", "bf16", "f32", "f64", "c128")
LAYOUTS = ("contiguous", "strided", "soa", "aos", "blocked", "csr", "csc", "mmap")
PARALLELISMS = ("single", "threads-2", "threads-4", "threads-8", "threads-auto", "processes", "gpu", "distributed")
HARDWARES = (
    "generic-cpu", "x86-sse42", "x86-avx2", "x86-avx512", "arm-neon", "arm-sve", "riscv-vector", "wasm-simd",
    "nvidia-cuda", "amd-hip", "apple-gpu", "integrated-gpu", "mobile-cpu", "server-numa", "embedded", "unknown-future",
)
OBJECTIVES = ("latency", "throughput", "memory", "energy", "accuracy", "startup", "portability", "balanced")


@dataclass(frozen=True, slots=True)
class FrontierAxes:
    languages: tuple[str, ...] = LANGUAGES
    strategies: tuple[str, ...] = STRATEGIES
    precisions: tuple[str, ...] = PRECISIONS
    layouts: tuple[str, ...] = LAYOUTS
    parallelisms: tuple[str, ...] = PARALLELISMS
    hardwares: tuple[str, ...] = HARDWARES
    objectives: tuple[str, ...] = OBJECTIVES

    def dimensions(self) -> tuple[tuple[str, ...], ...]:
        return (
            self.languages, self.strategies, self.precisions, self.layouts,
            self.parallelisms, self.hardwares, self.objectives,
        )

    @property
    def variants_per_algorithm(self) -> int:
        return reduce(mul, (len(axis) for axis in self.dimensions()), 1)


@dataclass(frozen=True, slots=True)
class LogicalFrontier:
    algorithm_ids: tuple[str, ...]
    axes: FrontierAxes = FrontierAxes()

    def __post_init__(self) -> None:
        if not self.algorithm_ids:
            raise ValueError("frontier requires at least one algorithm")
        if len(set(self.algorithm_ids)) != len(self.algorithm_ids):
            raise ValueError("algorithm_ids must be unique")
        if any(not axis for axis in self.axes.dimensions()):
            raise ValueError("frontier axes must be non-empty")

    @property
    def size(self) -> int:
        return len(self.algorithm_ids) * self.axes.variants_per_algorithm

    def address_at(self, global_index: int) -> VariantAddress:
        if global_index < 0 or global_index >= self.size:
            raise IndexError(f"index {global_index} outside frontier [0, {self.size})")
        per_algorithm = self.axes.variants_per_algorithm
        algorithm_position, remainder = divmod(global_index, per_algorithm)
        coordinates: list[str] = []
        for axis in reversed(self.axes.dimensions()):
            remainder, coordinate = divmod(remainder, len(axis))
            coordinates.append(axis[coordinate])
        language, strategy, precision, layout, parallelism, hardware, objective = reversed(coordinates)
        return VariantAddress(
            algorithm_id=self.algorithm_ids[algorithm_position],
            language=language,
            strategy=strategy,
            precision=precision,
            layout=layout,
            parallelism=parallelism,
            hardware=hardware,
            objective=objective,
        )

    def index_of(self, address: VariantAddress) -> int:
        try:
            algorithm_position = self.algorithm_ids.index(address.algorithm_id)
        except ValueError as exc:
            raise KeyError(address.algorithm_id) from exc
        values = (
            address.language, address.strategy, address.precision, address.layout,
            address.parallelism, address.hardware, address.objective,
        )
        index = algorithm_position
        for axis, value in zip(self.axes.dimensions(), values, strict=True):
            try:
                coordinate = axis.index(value)
            except ValueError as exc:
                raise KeyError(value) from exc
            index = index * len(axis) + coordinate
        return index

    def sample_indices(self, count: int, seed: int = 0) -> tuple[int, ...]:
        if count < 0:
            raise ValueError("count must be non-negative")
        if count >= self.size:
            return tuple(range(self.size))
        modulus = self.size
        step = (2 * seed + 1) % modulus or 1
        while _gcd(step, modulus) != 1:
            step += 2
        start = (seed * 0x9E3779B97F4A7C15) % modulus
        return tuple((start + step * index) % modulus for index in range(count))


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)
