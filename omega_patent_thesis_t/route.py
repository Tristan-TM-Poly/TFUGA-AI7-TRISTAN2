"""Small route helper."""

from __future__ import annotations

from .seed import PatentThesisSeed
from .stage import record_stage


def route_label(seed: PatentThesisSeed) -> str:
    stage = record_stage(seed)
    if stage == "A":
        return "add_claims"
    if stage == "B":
        return "add_targets"
    return "make_pack"
