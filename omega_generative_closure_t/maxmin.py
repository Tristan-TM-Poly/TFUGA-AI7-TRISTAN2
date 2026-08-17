from __future__ import annotations

from .core import MaxMinVector


def dominates(a: MaxMinVector, b: MaxMinVector) -> bool:
    ba = a.benefit_axes()
    bb = b.benefit_axes()
    ca = a.cost_axes()
    cb = b.cost_axes()
    weak = all(x >= y for x, y in zip(ba, bb)) and all(x <= y for x, y in zip(ca, cb))
    strict = any(x > y for x, y in zip(ba, bb)) or any(x < y for x, y in zip(ca, cb))
    return weak and strict


def pareto_frontier(candidates: dict[str, MaxMinVector]) -> tuple[str, ...]:
    names = sorted(candidates)
    return tuple(
        name
        for name in names
        if not any(other != name and dominates(candidates[other], candidates[name]) for other in names)
    )


def rank_power_density(candidates: dict[str, MaxMinVector]) -> tuple[tuple[str, float], ...]:
    return tuple(
        sorted(
            ((name, vector.power_density()) for name, vector in candidates.items()),
            key=lambda item: (-item[1], item[0]),
        )
    )
