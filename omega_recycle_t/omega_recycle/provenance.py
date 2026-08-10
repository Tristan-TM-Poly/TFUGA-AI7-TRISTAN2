from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    source_id: str
    source_url: str
    retrieved_at: str
    sha256: str
    license: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.source_url or not self.retrieved_at:
            raise ValueError("source_id, source_url and retrieved_at are required")
        if len(self.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.sha256.lower()):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_dataset_hash(records: object) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)
