"""Small level summary helper."""

from __future__ import annotations

from .risk import risk_level
from .seed import PatentThesisSeed


def level_summary(items: tuple[PatentThesisSeed, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        level = risk_level(item)
        out[level] = out.get(level, 0) + 1
    return out
