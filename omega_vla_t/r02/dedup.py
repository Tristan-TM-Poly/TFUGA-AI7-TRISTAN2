"""Content-addressed deduplication for generated Ω-VLA cells."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


IGNORED_VOLATILE_KEYS = frozenset(
    {
        "generated_at",
        "wall_time_seconds",
        "runner",
        "temporary_path",
    }
)


def normalize_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): normalize_payload(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key) not in IGNORED_VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [normalize_payload(item) for item in value]
    if isinstance(value, set):
        return sorted(normalize_payload(item) for item in value)
    if isinstance(value, float):
        if value == 0.0:
            return 0.0
        return float(f"{value:.15g}")
    return value


def content_digest(payload: Mapping[str, Any]) -> str:
    normalized = normalize_payload(payload)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class DeduplicationReport:
    accepted: tuple[Mapping[str, Any], ...]
    duplicates: tuple[Mapping[str, Any], ...]
    accepted_digests: tuple[str, ...]

    @property
    def input_count(self) -> int:
        return len(self.accepted) + len(self.duplicates)

    @property
    def duplicate_rate(self) -> float:
        if self.input_count == 0:
            return 0.0
        return len(self.duplicates) / self.input_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "accepted_count": len(self.accepted),
            "duplicate_count": len(self.duplicates),
            "duplicate_rate": self.duplicate_rate,
            "accepted_digests": list(self.accepted_digests),
        }


class ContentDeduplicator:
    """Stateful exact semantic-normal-form deduplicator."""

    def __init__(self, known_digests: Iterable[str] = ()) -> None:
        self._known = set(known_digests)

    def add(self, payload: Mapping[str, Any]) -> tuple[bool, str]:
        digest = content_digest(payload)
        if digest in self._known:
            return False, digest
        self._known.add(digest)
        return True, digest

    def filter(self, payloads: Iterable[Mapping[str, Any]]) -> DeduplicationReport:
        accepted: list[Mapping[str, Any]] = []
        duplicates: list[Mapping[str, Any]] = []
        digests: list[str] = []
        for payload in payloads:
            is_new, digest = self.add(payload)
            if is_new:
                accepted.append(payload)
                digests.append(digest)
            else:
                duplicates.append(payload)
        return DeduplicationReport(
            accepted=tuple(accepted),
            duplicates=tuple(duplicates),
            accepted_digests=tuple(digests),
        )

    def snapshot(self) -> tuple[str, ...]:
        return tuple(sorted(self._known))
