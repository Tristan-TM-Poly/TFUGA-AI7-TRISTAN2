"""Small shape helper."""

from __future__ import annotations

from .completeness import completeness_score
from .seed import PatentThesisSeed


def shape_label(seed: PatentThesisSeed) -> str:
    score = completeness_score(seed)
    if score >= 1.0:
        return "full"
    if score >= 0.6:
        return "partial"
    return "thin"
