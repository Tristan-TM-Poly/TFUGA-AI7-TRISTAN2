"""Finite multigraded-product laboratory for Ω-MULTI-GRADED-PRODUCT-T∞.

A homogeneous product A_p × A_q may emit several output degrees. The rule is
explicit data, so closure and associativity can be tested rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Iterable


@dataclass(frozen=True)
class OutputChannel:
    degree: int
    weight: float = 1.0


@dataclass(frozen=True)
class GradedElement:
    """Sparse scalar coordinate model over formal homogeneous basis elements."""

    components: tuple[tuple[int, float], ...]

    @classmethod
    def from_mapping(cls, values: dict[int, float]) -> "GradedElement":
        cleaned = tuple(
            sorted(
                (int(degree), float(value))
                for degree, value in values.items()
                if float(value) != 0.0
            )
        )
        return cls(cleaned)

    @classmethod
    def basis(cls, degree: int, coefficient: float = 1.0) -> "GradedElement":
        return cls.from_mapping({degree: coefficient})

    def as_dict(self) -> dict[int, float]:
        return dict(self.components)

    def norm(self) -> float:
        return sqrt(sum(value * value for _, value in self.components))


Rule = Callable[[int, int], Iterable[OutputChannel]]


def multiply_multigraded(
    left: GradedElement,
    right: GradedElement,
    rule: Rule,
) -> GradedElement:
    result: dict[int, float] = {}
    for p, left_value in left.components:
        for q, right_value in right.components:
            channels = tuple(rule(p, q))
            if not channels:
                continue
            for channel in channels:
                result[channel.degree] = result.get(channel.degree, 0.0) + (
                    left_value * right_value * channel.weight
                )
    return GradedElement.from_mapping(result)


def graded_associativity_defect(
    x: GradedElement,
    y: GradedElement,
    z: GradedElement,
    rule: Rule,
) -> GradedElement:
    left = multiply_multigraded(multiply_multigraded(x, y, rule), z, rule).as_dict()
    right = multiply_multigraded(x, multiply_multigraded(y, z, rule), rule).as_dict()
    degrees = set(left) | set(right)
    return GradedElement.from_mapping(
        {degree: left.get(degree, 0.0) - right.get(degree, 0.0) for degree in degrees}
    )


def standard_graded_rule(p: int, q: int) -> tuple[OutputChannel, ...]:
    """Ordinary degree-additive channel e_p e_q -> e_(p+q)."""

    return (OutputChannel(p + q, 1.0),)


def spectrum_rule(
    allowed_degrees: Callable[[int, int], Iterable[int]],
    *,
    weight: float = 1.0,
) -> Rule:
    """Build an equal-weight multi-output rule from a degree-spectrum function."""

    def rule(p: int, q: int) -> tuple[OutputChannel, ...]:
        return tuple(OutputChannel(int(degree), weight) for degree in allowed_degrees(p, q))

    return rule
