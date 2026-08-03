from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .models import SemanticProofKey


@dataclass(frozen=True)
class CacheEntry:
    key: str
    bundle_id: str
    residuals: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "bundle_id": self.bundle_id, "residuals": list(self.residuals)}


class SemanticProofCache:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def put(self, key: SemanticProofKey, bundle_id: str, *, residuals: tuple[str, ...] = ()) -> CacheEntry:
        entry = CacheEntry(key.key, bundle_id, tuple(residuals))
        self._entries[key.key] = entry
        return entry

    def get(self, key: SemanticProofKey) -> CacheEntry | None:
        return self._entries.get(key.key)

    def evaluate_reuse(self, expected: SemanticProofKey, candidate: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        for field in ("claim_digest", "code_slice_digest", "dependency_digest", "environment_class", "test_digest"):
            if str(candidate.get(field, "")) != getattr(expected, field):
                reasons.append(f"semantic proof cache mismatch: {field}")
        return (not reasons, tuple(reasons))
