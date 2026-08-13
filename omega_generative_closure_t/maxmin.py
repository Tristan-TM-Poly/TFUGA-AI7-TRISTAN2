from __future__ import annotations
from .core import MaxMinVector


def dominates(a: MaxMinVector, b: MaxMinVector) -> bool:
    ba = (a.verified_value, a.evidence, a.reuse, a.reachability, a.regenerability, a.fertility)
    bb = (b.verified_value, b.evidence, b.reuse, b.reachability, b.regenerability, b.fertility)
    ca = (a.cost, a.structural_debt, a.proof_debt, a.semantic_debt, a.uncertainty, a.irreversibility)
    cb = (b.cost, b.structural_debt, b.proof_debt, b.semantic_debt, b.uncertainty, b.irreversibility)
    weak = all(x >= y for x, y in zip(ba, bb)) and all(x <= y for x, y in zip(ca, cb))
    strict = any(x > y for x, y in zip(ba, bb)) or any(x < y for x, y in zip(ca, cb))
    return weak and strict


def pareto_frontier(candidates: dict[str, MaxMinVector]) -> tuple[str, ...]:
    names = sorted(candidates)
    return tuple(name for name in names if not any(other != name and dominates(candidates[other], candidates[name]) for other in names))


def rank_power_density(candidates: dict[str, MaxMinVector]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted(((n, v.power_density()) for n, v in candidates.items()), key=lambda x: (-x[1], x[0])))
