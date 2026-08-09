"""Finite orbit classification and invariant-completeness experiments."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Hashable, Iterable


Object = Hashable
Action = Callable[[Object], Object]
InvariantFn = Callable[[Object], Any]


def orbit(
    seed: Object,
    generators: Iterable[Action],
    *,
    universe: set[Object] | None = None,
) -> frozenset[Object]:
    actions = tuple(generators)
    seen = {seed}
    frontier = [seed]
    while frontier:
        current = frontier.pop()
        for action in actions:
            nxt = action(current)
            if universe is not None and nxt not in universe:
                raise ValueError("action left the declared finite universe")
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return frozenset(seen)


def orbit_partition(
    objects: Iterable[Object],
    generators: Iterable[Action],
) -> tuple[frozenset[Object], ...]:
    universe = set(objects)
    actions = tuple(generators)
    remaining = set(universe)
    parts: list[frozenset[Object]] = []
    while remaining:
        seed = next(iter(remaining))
        part = orbit(seed, actions, universe=universe)
        parts.append(part)
        remaining -= set(part)
    return tuple(parts)


def invariant_collisions(
    objects: Iterable[Object],
    generators: Iterable[Action],
    invariant: InvariantFn,
) -> tuple[tuple[Object, Object], ...]:
    """Pairs with equal invariant value but lying in different orbits."""

    points = tuple(objects)
    parts = orbit_partition(points, generators)
    orbit_id = {
        point: index
        for index, part in enumerate(parts)
        for point in part
    }
    collisions: list[tuple[Object, Object]] = []
    for left, right in combinations(points, 2):
        if invariant(left) == invariant(right) and orbit_id[left] != orbit_id[right]:
            collisions.append((left, right))
    return tuple(collisions)


def invariant_is_complete(
    objects: Iterable[Object],
    generators: Iterable[Action],
    invariant: InvariantFn,
) -> bool:
    """Finite completeness: equal invariant iff same orbit.

    Preservation is checked as well: all members of an orbit must have the same
    invariant value.
    """

    points = tuple(objects)
    parts = orbit_partition(points, generators)
    for part in parts:
        values = [invariant(point) for point in part]
        if values and any(value != values[0] for value in values[1:]):
            return False
    return not invariant_collisions(points, generators, invariant)


def minimal_complete_invariant_families(
    objects: Iterable[Object],
    generators: Iterable[Action],
    invariants: dict[str, InvariantFn],
) -> tuple[frozenset[str], ...]:
    """Exact finite T5 laboratory over a supplied invariant dictionary."""

    names = tuple(invariants)
    points = tuple(objects)
    minima: list[frozenset[str]] = []
    for size in range(1, len(names) + 1):
        for combo in combinations(names, size):
            candidate = frozenset(combo)
            if any(previous <= candidate for previous in minima):
                continue

            def joint(point: Object) -> tuple[Any, ...]:
                return tuple(invariants[name](point) for name in combo)

            if invariant_is_complete(points, generators, joint):
                minima.append(candidate)
    return tuple(minima)
