"""Executable seed for *La Loi du Minimum Suffisant*.

This module deliberately solves only a bounded, finite version of the book's
"minimum generating basis" idea.  It is an engineering experiment, not a
proof that a general system can always be compressed optimally.

A component contributes a finite set of declared capabilities and has a
non-negative persistence cost.  Given a required capability set, the solver
finds an exact minimum-cardinality sufficient subset, then breaks ties by
minimum total cost and finally by lexical component name for determinism.

The exhaustive search is intentionally capped: the general set-cover family
is combinatorial, so refusing oversized instances is part of the OAK contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Component:
    """A finite component used by the bounded experiment."""

    name: str
    capabilities: frozenset[str]
    persistence_cost: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("component name must be non-empty")
        if self.persistence_cost < 0:
            raise ValueError("persistence_cost must be non-negative")


@dataclass(frozen=True)
class BasisResult:
    """Exact result for one bounded finite instance."""

    components: tuple[str, ...]
    covered_capabilities: frozenset[str]
    total_cost: float


def _coverage(items: Iterable[Component]) -> frozenset[str]:
    covered: set[str] = set()
    for item in items:
        covered.update(item.capabilities)
    return frozenset(covered)


def find_minimum_sufficient_basis(
    components: Sequence[Component],
    required_capabilities: Iterable[str],
    *,
    max_components: int = 20,
) -> BasisResult:
    """Return the exact bounded minimum sufficient basis.

    Ordering criterion:
      1. minimum number of persistent components;
      2. minimum summed persistence cost;
      3. lexical component-name tuple for deterministic replay.

    Raises:
        ValueError: malformed/duplicate input, impossible coverage, or an
            instance larger than ``max_components``.
    """

    required = frozenset(required_capabilities)
    if max_components < 0:
        raise ValueError("max_components must be non-negative")
    if len(components) > max_components:
        raise ValueError(
            f"bounded exact solver refuses {len(components)} components; "
            f"limit is {max_components}"
        )

    names = [component.name for component in components]
    if len(names) != len(set(names)):
        raise ValueError("component names must be unique")

    if not required:
        return BasisResult((), frozenset(), 0.0)

    universe = _coverage(components)
    missing = required - universe
    if missing:
        raise ValueError(f"required capabilities are unreachable: {sorted(missing)}")

    best: tuple[tuple[int, float, tuple[str, ...]], tuple[Component, ...]] | None = None

    for size in range(1, len(components) + 1):
        for subset in combinations(components, size):
            covered = _coverage(subset)
            if not required.issubset(covered):
                continue
            names_tuple = tuple(sorted(component.name for component in subset))
            total_cost = sum(component.persistence_cost for component in subset)
            score = (size, total_cost, names_tuple)
            if best is None or score < best[0]:
                best = (score, subset)
        if best is not None:
            break

    assert best is not None  # reachability was checked above
    _, subset = best
    return BasisResult(
        components=tuple(sorted(component.name for component in subset)),
        covered_capabilities=_coverage(subset),
        total_cost=sum(component.persistence_cost for component in subset),
    )


def necessity_by_ablation(
    selected: Sequence[Component],
    required_capabilities: Iterable[str],
) -> Mapping[str, frozenset[str]]:
    """Return the required capabilities lost when each component is removed.

    A component has an empty lost-capability set when its declared contribution
    is redundant *within the currently selected coalition*.  This is a local
    ablation result only; it does not establish global uselessness across other
    scales, contexts, future goals, safety margins, or optionality.
    """

    required = frozenset(required_capabilities)
    baseline = _coverage(selected)
    if not required.issubset(baseline):
        missing = required - baseline
        raise ValueError(f"selected coalition is already insufficient: {sorted(missing)}")

    losses: dict[str, frozenset[str]] = {}
    for index, component in enumerate(selected):
        without_component = selected[:index] + selected[index + 1 :]
        remaining = _coverage(without_component)
        losses[component.name] = frozenset(required - remaining)
    return losses


def demo() -> BasisResult:
    """Small deterministic cross-domain-style fixture for manual replay."""

    candidates = [
        Component("observe", frozenset({"measure", "trace"}), 1.0),
        Component("verify", frozenset({"proof", "trace"}), 1.2),
        Component("regenerate", frozenset({"restore", "trace"}), 1.1),
        Component("ornamental", frozenset({"presentation"}), 0.2),
    ]
    required = {"measure", "proof", "restore"}
    return find_minimum_sufficient_basis(candidates, required)


if __name__ == "__main__":
    result = demo()
    print("minimum_basis=", ",".join(result.components))
    print("total_cost=", result.total_cost)
    print("covered=", ",".join(sorted(result.covered_capabilities)))
