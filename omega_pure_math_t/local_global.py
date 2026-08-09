"""Finite local-to-global gluing laboratory.

This is a small exact analogue of a sheaf-style compatibility problem: local
sections are mappings on overlapping finite domains, and gluing either returns a
unique merged section or an explicit overlap obstruction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable, Iterable


Point = Hashable


@dataclass(frozen=True)
class Section:
    name: str
    values: tuple[tuple[Point, Any], ...]

    @classmethod
    def from_mapping(cls, name: str, values: dict[Point, Any]) -> "Section":
        return cls(name, tuple(values.items()))

    def as_dict(self) -> dict[Point, Any]:
        return dict(self.values)

    @property
    def domain(self) -> frozenset[Point]:
        return frozenset(point for point, _ in self.values)


@dataclass(frozen=True)
class GluingObstruction:
    point: Point
    left_section: str
    right_section: str
    left_value: Any
    right_value: Any


def compatibility_obstructions(
    sections: Iterable[Section],
) -> tuple[GluingObstruction, ...]:
    items = tuple(sections)
    obstructions: list[GluingObstruction] = []
    for i, left in enumerate(items):
        left_values = left.as_dict()
        for right in items[i + 1 :]:
            right_values = right.as_dict()
            for point in left.domain & right.domain:
                if left_values[point] != right_values[point]:
                    obstructions.append(
                        GluingObstruction(
                            point,
                            left.name,
                            right.name,
                            left_values[point],
                            right_values[point],
                        )
                    )
    return tuple(obstructions)


def glue_sections(sections: Iterable[Section]) -> Section:
    """Glue exactly compatible finite sections or raise with an obstruction."""

    items = tuple(sections)
    obstructions = compatibility_obstructions(items)
    if obstructions:
        first = obstructions[0]
        raise ValueError(
            f"gluing obstruction at {first.point!r}: "
            f"{first.left_section}={first.left_value!r} != "
            f"{first.right_section}={first.right_value!r}"
        )
    merged: dict[Point, Any] = {}
    for section in items:
        merged.update(section.as_dict())
    return Section.from_mapping("global", merged)


def cover_is_complete(sections: Iterable[Section], universe: Iterable[Point]) -> bool:
    covered: set[Point] = set()
    for section in sections:
        covered.update(section.domain)
    return covered == set(universe)
