"""Completeness helper for record seeds."""

from __future__ import annotations

from .seed import PatentThesisSeed


def missing_fields(seed: PatentThesisSeed) -> tuple[str, ...]:
    missing: list[str] = []
    if not seed.core_problem:
        missing.append("core_problem")
    if not seed.core_solution:
        missing.append("core_solution")
    if not seed.independent_claims:
        missing.append("independent_claims")
    if not seed.prototype_targets:
        missing.append("prototype_targets")
    if not seed.oak_risks:
        missing.append("oak_risks")
    return tuple(missing)


def completeness_score(seed: PatentThesisSeed) -> float:
    total = 5
    missing = len(missing_fields(seed))
    return (total - missing) / total
