from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

ARTIFACT_CLASSES = (
    "claim", "derivation", "schema", "code", "tests", "benchmark",
    "data_or_figure", "document", "example", "cli_or_api", "ci",
    "provenance", "oak_receipt", "negative_memory", "integration_bridge",
    "regeneration_manifest",
)

@dataclass(frozen=True)
class LadderResult:
    n: int
    target: int
    covered: tuple[str, ...]
    missing: tuple[str, ...]
    next_target: int
    marginal_verified_gain: float | None
    saturation_candidate: bool


def evaluate_ladder(n: int, covered: Iterable[str], *, verified_gain_n: float | None = None,
                    verified_gain_next: float | None = None, cost_next: float | None = None,
                    epsilon: float = 0.01) -> LadderResult:
    if n < 0:
        raise ValueError("n must be non-negative")
    target = 2 ** n
    next_target = 2 ** (n + 1)
    known = tuple(sorted(set(covered) & set(ARTIFACT_CLASSES)))
    missing = tuple(x for x in ARTIFACT_CLASSES[:min(next_target, len(ARTIFACT_CLASSES))] if x not in known)
    mvg = None
    saturation = False
    if verified_gain_n is not None and verified_gain_next is not None and cost_next is not None:
        vals = (verified_gain_n, verified_gain_next, cost_next, epsilon)
        if not all(isfinite(v) for v in vals) or cost_next <= 0 or epsilon < 0:
            raise ValueError("finite gains, positive cost and non-negative epsilon required")
        mvg = (verified_gain_next - verified_gain_n) / cost_next
        saturation = mvg <= epsilon and not missing
    return LadderResult(n, target, known, missing, next_target, mvg, saturation)
