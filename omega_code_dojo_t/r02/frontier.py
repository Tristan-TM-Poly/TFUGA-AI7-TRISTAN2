from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Iterator, Mapping, Sequence

from .models import FrontierCell


def _names(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(f"{prefix}_{index:03d}" for index in range(count))


@dataclass(frozen=True)
class FrontierAxis:
    name: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("axis name must be non-empty")
        if not self.values:
            raise ValueError(f"axis {self.name} must contain values")
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"axis {self.name} contains duplicate values")


@dataclass(frozen=True)
class LogicalFrontier:
    domains: FrontierAxis
    archetypes: FrontierAxis
    difficulty_bands: FrontierAxis
    languages: FrontierAxis
    execution_regimes: FrontierAxis
    mutation_families: FrontierAxis

    @property
    def axes(self) -> tuple[FrontierAxis, ...]:
        return (
            self.domains,
            self.archetypes,
            self.difficulty_bands,
            self.languages,
            self.execution_regimes,
            self.mutation_families,
        )

    @property
    def logical_cell_count(self) -> int:
        return prod(len(axis.values) for axis in self.axes)

    def axis_cardinalities(self) -> dict[str, int]:
        return {axis.name: len(axis.values) for axis in self.axes}

    def iter_cells(self) -> Iterator[FrontierCell]:
        for values in product(*(axis.values for axis in self.axes)):
            yield FrontierCell(*values)

    def cell_at(self, ordinal: int) -> FrontierCell:
        if ordinal < 0 or ordinal >= self.logical_cell_count:
            raise IndexError("frontier ordinal outside logical address space")
        radices = [len(axis.values) for axis in self.axes]
        indexes = [0] * len(radices)
        remainder = ordinal
        for position in range(len(radices) - 1, -1, -1):
            indexes[position] = remainder % radices[position]
            remainder //= radices[position]
        selected = [axis.values[index] for axis, index in zip(self.axes, indexes)]
        return FrontierCell(*selected)

    def ordinal_of(self, cell: FrontierCell) -> int:
        values = (
            cell.domain,
            cell.archetype,
            cell.difficulty_band,
            cell.language,
            cell.execution_regime,
            cell.mutation_family,
        )
        ordinal = 0
        for axis, value in zip(self.axes, values):
            ordinal *= len(axis.values)
            try:
                ordinal += axis.values.index(value)
            except ValueError as exc:
                raise ValueError(f"unknown {axis.name} value: {value}") from exc
        return ordinal

    def extended(self, additions: Mapping[str, Sequence[str]]) -> "LogicalFrontier":
        axes: dict[str, FrontierAxis] = {}
        for axis in self.axes:
            incoming = tuple(additions.get(axis.name, ()))
            merged = axis.values + tuple(value for value in incoming if value not in axis.values)
            axes[axis.name] = FrontierAxis(axis.name, merged)
        unknown = set(additions) - set(axes)
        if unknown:
            raise ValueError(f"unknown frontier axes: {sorted(unknown)}")
        return LogicalFrontier(
            domains=axes["domains"],
            archetypes=axes["archetypes"],
            difficulty_bands=axes["difficulty_bands"],
            languages=axes["languages"],
            execution_regimes=axes["execution_regimes"],
            mutation_families=axes["mutation_families"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "logical_cell_count": self.logical_cell_count,
            "axis_cardinalities": self.axis_cardinalities(),
            "axes": {axis.name: list(axis.values) for axis in self.axes},
        }


CORE_DOMAINS = (
    "arrays",
    "strings",
    "hashing",
    "sorting",
    "search",
    "graphs",
    "trees",
    "dynamic_programming",
    "greedy",
    "number_theory",
    "combinatorics",
    "geometry",
    "linear_algebra",
    "probability",
    "optimization",
    "concurrency",
)
CORE_ARCHETYPES = (
    "decision",
    "construction",
    "optimization",
    "counting",
    "enumeration",
    "verification",
    "inverse",
    "online",
    "streaming",
    "dynamic",
    "approximation",
    "adversarial",
    "proof",
    "repair",
    "compression",
    "translation",
)
CORE_LANGUAGES = (
    "python",
    "rust",
    "cpp",
    "c",
    "java",
    "go",
    "javascript",
    "typescript",
    "csharp",
    "kotlin",
    "ruby",
    "julia",
    "haskell",
    "swift",
    "scala",
    "lean",
)
CORE_REGIMES = (
    "deterministic",
    "property",
    "metamorphic",
    "differential",
    "fuzz",
    "mutation",
    "bounded_formal",
    "complexity",
)
CORE_MUTATIONS = (
    "off_by_one",
    "comparison_flip",
    "branch_delete",
    "wrong_identity",
    "sign_flip",
    "index_swap",
    "termination_change",
    "numeric_narrowing",
    "overflow",
    "unstable_order",
    "shallow_copy",
    "memo_delete",
    "cache_alias",
    "inadmissible_heuristic",
    "empty_case_delete",
    "boundary_shift",
)

DEFAULT_FRONTIER = LogicalFrontier(
    domains=FrontierAxis("domains", CORE_DOMAINS + _names("domain", 112)),
    archetypes=FrontierAxis("archetypes", CORE_ARCHETYPES + _names("archetype", 48)),
    difficulty_bands=FrontierAxis("difficulty_bands", _names("difficulty", 32)),
    languages=FrontierAxis("languages", CORE_LANGUAGES + _names("language", 8)),
    execution_regimes=FrontierAxis(
        "execution_regimes", CORE_REGIMES + _names("regime", 8)
    ),
    mutation_families=FrontierAxis(
        "mutation_families", CORE_MUTATIONS + _names("mutation", 16)
    ),
)
