"""Dense higher-order tensor permutations and exact (anti)symmetrizers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product
from math import factorial, prod
from typing import Iterable, Sequence


def _strides(shape: Sequence[int]) -> tuple[int, ...]:
    result = []
    running = 1
    for size in reversed(shape):
        result.append(running)
        running *= size
    return tuple(reversed(result))


def _flat_index(index: Sequence[int], shape: Sequence[int]) -> int:
    if len(index) != len(shape):
        raise ValueError("index rank must match tensor rank")
    strides = _strides(shape)
    offset = 0
    for coordinate, size, stride in zip(index, shape, strides, strict=True):
        if not 0 <= coordinate < size:
            raise IndexError(index)
        offset += coordinate * stride
    return offset


def permutation_sign(permutation: Sequence[int]) -> int:
    perm = tuple(permutation)
    if sorted(perm) != list(range(len(perm))):
        raise ValueError("invalid permutation")
    inversions = sum(
        1
        for i in range(len(perm))
        for j in range(i + 1, len(perm))
        if perm[i] > perm[j]
    )
    return -1 if inversions % 2 else 1


@dataclass(frozen=True)
class DenseTensor:
    shape: tuple[int, ...]
    data: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.shape or any(size <= 0 for size in self.shape):
            raise ValueError("tensor shape must contain positive dimensions")
        if len(self.data) != prod(self.shape):
            raise ValueError("data length does not match shape")

    @property
    def rank(self) -> int:
        return len(self.shape)

    @property
    def dimension(self) -> int:
        return len(self.data)

    def at(self, index: Sequence[int]) -> float:
        return self.data[_flat_index(index, self.shape)]

    def indices(self) -> Iterable[tuple[int, ...]]:
        return product(*(range(size) for size in self.shape))

    def permute_axes(self, permutation: Sequence[int]) -> "DenseTensor":
        perm = tuple(permutation)
        if sorted(perm) != list(range(self.rank)):
            raise ValueError("invalid axis permutation")
        new_shape = tuple(self.shape[axis] for axis in perm)
        inverse = tuple(perm.index(axis) for axis in range(self.rank))
        values = []
        for new_index in product(*(range(size) for size in new_shape)):
            old_index = tuple(new_index[inverse[axis]] for axis in range(self.rank))
            values.append(self.at(old_index))
        return DenseTensor(new_shape, tuple(values))

    def add(self, other: "DenseTensor") -> "DenseTensor":
        if self.shape != other.shape:
            raise ValueError("tensor shapes must match")
        return DenseTensor(
            self.shape,
            tuple(a + b for a, b in zip(self.data, other.data, strict=True)),
        )

    def scale(self, scalar: float) -> "DenseTensor":
        factor = float(scalar)
        return DenseTensor(self.shape, tuple(factor * value for value in self.data))

    def subtract(self, other: "DenseTensor") -> "DenseTensor":
        return self.add(other.scale(-1.0))

    def norm_squared(self) -> float:
        return sum(value * value for value in self.data)

    def symmetrize(self, axes: Sequence[int] | None = None) -> "DenseTensor":
        selected = tuple(range(self.rank)) if axes is None else tuple(axes)
        return self._project_permutation_type(selected, alternating=False)

    def antisymmetrize(self, axes: Sequence[int] | None = None) -> "DenseTensor":
        selected = tuple(range(self.rank)) if axes is None else tuple(axes)
        return self._project_permutation_type(selected, alternating=True)

    def _project_permutation_type(
        self,
        axes: tuple[int, ...],
        *,
        alternating: bool,
    ) -> "DenseTensor":
        if len(set(axes)) != len(axes) or any(axis < 0 or axis >= self.rank for axis in axes):
            raise ValueError("invalid selected axes")
        if len({self.shape[axis] for axis in axes}) > 1:
            raise ValueError("selected axes must have equal dimensions")
        result = DenseTensor(self.shape, tuple(0.0 for _ in self.data))
        for local_permutation in permutations(range(len(axes))):
            global_permutation = list(range(self.rank))
            for target_position, source_local in enumerate(local_permutation):
                global_permutation[axes[target_position]] = axes[source_local]
            term = self.permute_axes(global_permutation)
            sign = permutation_sign(local_permutation) if alternating else 1
            result = result.add(term.scale(sign))
        return result.scale(1.0 / factorial(len(axes)))


def outer_many(vectors: Sequence[Sequence[float]]) -> DenseTensor:
    if not vectors or any(not vector for vector in vectors):
        raise ValueError("outer_many requires non-empty vectors")
    shape = tuple(len(vector) for vector in vectors)
    values = []
    for index in product(*(range(size) for size in shape)):
        value = 1.0
        for axis, coordinate in enumerate(index):
            value *= float(vectors[axis][coordinate])
        values.append(value)
    return DenseTensor(shape, tuple(values))
