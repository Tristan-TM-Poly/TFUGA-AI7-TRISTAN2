"""Exact small-N Shapley attribution for measured optimization ablations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import itertools
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class TransformationCredit:
    transformation_id: str
    shapley_credit: float
    status: str = "optimization-credit-attribution"
    oak_warning: str = (
        "Shapley credit attributes the supplied coalition value function. It "
        "does not establish a physical or software-causal mechanism unless the "
        "coalition experiments themselves identify that mechanism."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def shapley_optimization_credit(
    transformations: Sequence[str],
    coalition_values: Mapping[frozenset[str], float],
    *,
    max_transformations: int = 8,
) -> tuple[TransformationCredit, ...]:
    ids = tuple(transformations)
    if len(ids) != len(set(ids)):
        raise ValueError("transformations must be unique")
    if len(ids) > max_transformations:
        raise ValueError(f"exact Shapley attribution is capped at {max_transformations}")
    required = {
        frozenset(combo)
        for r in range(len(ids) + 1)
        for combo in itertools.combinations(ids, r)
    }
    missing = required - set(coalition_values)
    if missing:
        raise ValueError(f"missing {len(missing)} coalition values")

    n = len(ids)
    if n == 0:
        return ()
    rows: list[TransformationCredit] = []
    for item in ids:
        credit = 0.0
        others = tuple(x for x in ids if x != item)
        for r in range(len(others) + 1):
            for combo in itertools.combinations(others, r):
                coalition = frozenset(combo)
                weight = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                marginal = float(coalition_values[coalition | {item}]) - float(coalition_values[coalition])
                credit += weight * marginal
        rows.append(TransformationCredit(item, credit))
    return tuple(rows)
