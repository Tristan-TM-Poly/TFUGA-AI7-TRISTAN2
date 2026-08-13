from __future__ import annotations

from collections.abc import Iterable
from .core import ClosureReport, PrimitiveNecessity, Rule


def compute_closure(seeds: Iterable[str], rules: Iterable[Rule]) -> ClosureReport:
    seed_set = frozenset(seeds)
    reachable = set(seed_set)
    ordered_rules = tuple(rules)
    fired: list[str] = []
    fired_set: set[str] = set()
    rounds = 0
    for _ in range(len(ordered_rules) + 1):
        rounds += 1
        changed = False
        for rule in ordered_rules:
            if rule.name not in fired_set and rule.requires <= reachable:
                before = len(reachable)
                reachable.update(rule.produces)
                fired.append(rule.name)
                fired_set.add(rule.name)
                changed = changed or len(reachable) != before
        if not changed:
            break
    return ClosureReport(seed_set, frozenset(reachable), tuple(fired), rounds)


def primitive_necessity(seeds: Iterable[str], rules: Iterable[Rule]) -> tuple[PrimitiveNecessity, ...]:
    seed_set = frozenset(seeds)
    full = compute_closure(seed_set, rules)
    out: list[PrimitiveNecessity] = []
    for primitive in sorted(seed_set):
        reduced = frozenset(x for x in seed_set if x != primitive)
        ablated = compute_closure(reduced, rules)
        lost = frozenset(full.reachable.difference(ablated.reachable))
        out.append(PrimitiveNecessity(primitive, len(full.reachable), len(ablated.reachable), lost))
    return tuple(out)
