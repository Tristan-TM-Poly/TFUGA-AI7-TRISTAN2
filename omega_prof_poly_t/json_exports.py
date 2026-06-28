"""Deterministic JSON exporters for Ω-ABSORB-POLY-PROF-T."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def to_plain_data(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: to_plain_data(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_plain_data(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple, set)):
        return [to_plain_data(item) for item in value]
    return value


def to_deterministic_json(value: Any) -> str:
    """Return deterministic, stable JSON for snapshot tests and GitHub reports."""

    return json.dumps(to_plain_data(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def packet_digest(value: Any) -> str:
    """Tiny deterministic digest for tracking packet changes without extra deps."""

    text = to_deterministic_json(value)
    total = 0
    for index, char in enumerate(text, start=1):
        total = (total + index * ord(char)) % 1_000_000_007
    return f"pkt-{total:010d}"
