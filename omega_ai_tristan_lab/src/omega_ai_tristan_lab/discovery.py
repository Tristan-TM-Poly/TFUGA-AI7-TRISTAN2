"""Negative-memory discovery reporting for Tristan plugins."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DiscoveryFailure:
    entrypoint: str
    value: str
    distribution: str
    version: str
    error_type: str
    error_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    loaded: tuple[str, ...]
    failed: tuple[DiscoveryFailure, ...]
    expected_missing: tuple[str, ...]
    mode: str

    @property
    def ok(self) -> bool:
        if self.mode == "oak-strict":
            return not self.failed and not self.expected_missing
        if self.mode == "strict":
            return not self.failed
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "loaded": list(self.loaded),
            "failed": [item.to_dict() for item in self.failed],
            "expected_missing": list(self.expected_missing),
            "mode": self.mode,
            "ok": self.ok,
        }
