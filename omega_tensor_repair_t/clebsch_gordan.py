"""Dimension-level SU(2) Clebsch-Gordan branching rules."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any


@dataclass(frozen=True)
class SU2Irrep:
    dimension: int

    def __post_init__(self) -> None:
        if self.dimension <= 0:
            raise ValueError("SU(2) irrep dimension must be positive")

    @property
    def spin(self) -> Fraction:
        return Fraction(self.dimension - 1, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "spin_numerator": self.spin.numerator,
            "spin_denominator": self.spin.denominator,
        }


@dataclass(frozen=True)
class ClebschGordanBranch:
    left: SU2Irrep
    right: SU2Irrep
    outputs: tuple[SU2Irrep, ...]

    @property
    def input_dimension(self) -> int:
        return self.left.dimension * self.right.dimension

    @property
    def output_dimension(self) -> int:
        return sum(output.dimension for output in self.outputs)

    @property
    def exact(self) -> bool:
        return self.input_dimension == self.output_dimension

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "outputs": [output.to_dict() for output in self.outputs],
            "input_dimension": self.input_dimension,
            "output_dimension": self.output_dimension,
            "exact": self.exact,
            "boundary": "Dimension branching only; no numerical Clebsch-Gordan coefficients are claimed.",
        }


def su2_clebsch_gordan(left_dimension: int, right_dimension: int) -> ClebschGordanBranch:
    left = SU2Irrep(left_dimension)
    right = SU2Irrep(right_dimension)
    largest = left_dimension + right_dimension - 1
    smallest = abs(left_dimension - right_dimension) + 1
    outputs = tuple(
        SU2Irrep(dimension)
        for dimension in range(largest, smallest - 1, -2)
    )
    branch = ClebschGordanBranch(left, right, outputs)
    if not branch.exact:
        raise AssertionError("internal SU(2) dimension conservation failure")
    return branch
