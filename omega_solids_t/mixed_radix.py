from __future__ import annotations
from dataclasses import dataclass
from functools import reduce
from operator import mul
from typing import Iterator, Sequence

@dataclass(frozen=True)
class MixedRadixSpace:
    radices: tuple[int, ...]
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.radices or any(r <= 0 for r in self.radices):
            raise ValueError("all radices must be positive")
        if self.labels and len(self.labels) != len(self.radices):
            raise ValueError("labels and radices must have the same length")

    @property
    def cardinality(self) -> int:
        return reduce(mul, self.radices, 1)

    def decode(self, index: int) -> tuple[int, ...]:
        if not 0 <= index < self.cardinality:
            raise IndexError(index)
        digits = [0] * len(self.radices)
        value = index
        for pos in range(len(self.radices)-1, -1, -1):
            value, digits[pos] = divmod(value, self.radices[pos])
        return tuple(digits)

    def encode(self, digits: Sequence[int]) -> int:
        if len(digits) != len(self.radices):
            raise ValueError("wrong digit count")
        result = 0
        for digit, radix in zip(digits, self.radices):
            if not 0 <= digit < radix:
                raise ValueError(f"digit {digit} outside radix {radix}")
            result = result * radix + digit
        return result

    def as_mapping(self, index: int) -> dict[str, int]:
        digits = self.decode(index)
        labels = self.labels or tuple(f"axis_{i}" for i in range(len(digits)))
        return dict(zip(labels, digits))

    def iter_range(self, start: int = 0, stop: int | None = None, step: int = 1) -> Iterator[tuple[int, tuple[int, ...]]]:
        if step <= 0:
            raise ValueError("step must be positive")
        stop = self.cardinality if stop is None else min(stop, self.cardinality)
        if start < 0 or stop < start:
            raise ValueError("invalid range")
        for index in range(start, stop, step):
            yield index, self.decode(index)
