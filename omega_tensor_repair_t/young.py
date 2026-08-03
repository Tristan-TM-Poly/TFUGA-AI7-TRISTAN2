"""Young-diagram combinatorics and finite row/column symmetry operators."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations, product
from math import factorial
from typing import Iterable, Sequence

from .higher_order import DenseTensor, permutation_sign


@dataclass(frozen=True)
class YoungDiagram:
    rows: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.rows or any(length <= 0 for length in self.rows):
            raise ValueError("Young diagram rows must be positive")
        if any(left < right for left, right in zip(self.rows, self.rows[1:])):
            raise ValueError("Young diagram rows must be non-increasing")

    @property
    def boxes(self) -> int:
        return sum(self.rows)

    @property
    def columns(self) -> tuple[int, ...]:
        return tuple(sum(1 for row in self.rows if row > col) for col in range(self.rows[0]))

    def cells(self) -> tuple[tuple[int, int], ...]:
        return tuple((row, col) for row, length in enumerate(self.rows) for col in range(length))

    def hook_length(self, row: int, col: int) -> int:
        if row < 0 or row >= len(self.rows) or col < 0 or col >= self.rows[row]:
            raise IndexError((row, col))
        right = self.rows[row] - col - 1
        below = sum(1 for later in self.rows[row + 1 :] if later > col)
        return 1 + right + below

    def hook_product(self) -> int:
        result = 1
        for row, col in self.cells():
            result *= self.hook_length(row, col)
        return result

    def standard_tableau_count(self) -> int:
        return factorial(self.boxes) // self.hook_product()

    def schur_dimension(self, ambient_dimension: int) -> int:
        """Dimension of the polynomial GL(d) irrep via hook-content formula."""

        if ambient_dimension < 0:
            raise ValueError("ambient dimension must be non-negative")
        value = Fraction(1, 1)
        for row, col in self.cells():
            content_factor = ambient_dimension + col - row
            if content_factor <= 0:
                return 0
            value *= Fraction(content_factor, self.hook_length(row, col))
        if value.denominator != 1:
            raise AssertionError("hook-content formula did not produce an integer")
        return value.numerator

    def canonical_tableau(self) -> tuple[tuple[int, ...], ...]:
        next_value = 0
        rows: list[tuple[int, ...]] = []
        for length in self.rows:
            rows.append(tuple(range(next_value, next_value + length)))
            next_value += length
        return tuple(rows)


def partitions(total: int, maximum: int | None = None) -> tuple[YoungDiagram, ...]:
    if total <= 0:
        raise ValueError("total must be positive")

    def generate(remaining: int, upper: int, prefix: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
        if remaining == 0:
            yield prefix
            return
        for value in range(min(remaining, upper), 0, -1):
            yield from generate(remaining - value, value, prefix + (value,))

    upper = total if maximum is None else min(total, maximum)
    return tuple(YoungDiagram(rows) for rows in generate(total, upper, tuple()))


def _disjoint_group_permutations(groups: Sequence[Sequence[int]], rank: int) -> tuple[tuple[int, ...], ...]:
    local_permutations = [tuple(permutations(group)) for group in groups]
    results: list[tuple[int, ...]] = []
    for choices in product(*local_permutations):
        mapping = list(range(rank))
        for group, choice in zip(groups, choices, strict=True):
            for target, source in zip(group, choice, strict=True):
                mapping[target] = source
        results.append(tuple(mapping))
    return tuple(results)


def row_groups(diagram: YoungDiagram) -> tuple[tuple[int, ...], ...]:
    return diagram.canonical_tableau()


def column_groups(diagram: YoungDiagram) -> tuple[tuple[int, ...], ...]:
    tableau = diagram.canonical_tableau()
    return tuple(
        tuple(tableau[row][col] for row in range(len(tableau)) if col < len(tableau[row]))
        for col in range(diagram.rows[0])
    )


def _add(left: DenseTensor, right: DenseTensor) -> DenseTensor:
    return left.add(right)


def _zero_like(tensor: DenseTensor) -> DenseTensor:
    return DenseTensor(tensor.shape, tuple(0.0 for _ in tensor.data))


def row_symmetrize(tensor: DenseTensor, diagram: YoungDiagram) -> DenseTensor:
    if tensor.rank != diagram.boxes:
        raise ValueError("tensor rank must equal number of Young boxes")
    groups = row_groups(diagram)
    permutations_all = _disjoint_group_permutations(groups, tensor.rank)
    result = _zero_like(tensor)
    for permutation in permutations_all:
        result = _add(result, tensor.permute_axes(permutation))
    return result.scale(1.0 / len(permutations_all))


def column_antisymmetrize(tensor: DenseTensor, diagram: YoungDiagram) -> DenseTensor:
    if tensor.rank != diagram.boxes:
        raise ValueError("tensor rank must equal number of Young boxes")
    groups = column_groups(diagram)
    permutations_all = _disjoint_group_permutations(groups, tensor.rank)
    result = _zero_like(tensor)
    for permutation in permutations_all:
        sign = permutation_sign(permutation)
        result = _add(result, tensor.permute_axes(permutation).scale(sign))
    return result.scale(1.0 / len(permutations_all))


def young_operator(tensor: DenseTensor, diagram: YoungDiagram) -> DenseTensor:
    """Apply normalized row symmetrization followed by column antisymmetrization.

    For one-row and one-column diagrams this is an exact orthogonal projector.
    For mixed diagrams it is a deterministic Young symmetry operator; R0.3 does
    not claim orthogonal normalization or universal idempotence.
    """

    return column_antisymmetrize(row_symmetrize(tensor, diagram), diagram)


def young_dimension_atlas(order: int, ambient_dimension: int) -> tuple[dict[str, object], ...]:
    atlas = []
    for diagram in partitions(order):
        atlas.append(
            {
                "partition": list(diagram.rows),
                "boxes": diagram.boxes,
                "standard_tableaux": diagram.standard_tableau_count(),
                "schur_dimension": diagram.schur_dimension(ambient_dimension),
                "hook_product": diagram.hook_product(),
            }
        )
    return tuple(atlas)
