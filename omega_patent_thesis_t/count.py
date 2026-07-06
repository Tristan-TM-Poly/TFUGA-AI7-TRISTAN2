"""Small count helper."""

from __future__ import annotations

from .seed import PatentThesisSeed


def count_records(items: tuple[PatentThesisSeed, ...]) -> int:
    for item in items:
        item.validate()
    return len(items)
