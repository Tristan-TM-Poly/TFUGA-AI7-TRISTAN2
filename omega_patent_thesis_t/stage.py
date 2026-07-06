"""Small record stage helper."""

from __future__ import annotations

from .seed import PatentThesisSeed


def record_stage(seed: PatentThesisSeed) -> str:
    seed.validate()
    if seed.independent_claims and seed.prototype_targets:
        return "C"
    if seed.independent_claims:
        return "B"
    return "A"
