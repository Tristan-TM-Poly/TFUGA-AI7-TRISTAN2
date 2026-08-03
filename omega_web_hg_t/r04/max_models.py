from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_object(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NormalizedRecord:
    source_id: str
    record_id: str
    canonical_url: str | None = None
    title: str | None = None
    record_type: str | None = None
    issued: str | None = None
    updated: str | None = None
    license: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    topics: tuple[str, ...] = ()
    request_receipt_id: str = ""
    source_payload_sha256: str = ""
    epistemic_status: str = "metadata_extracted_not_verified"

    @property
    def digest(self) -> str:
        return digest_object(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "digest": self.digest}


@dataclass(frozen=True)
class RequestReceipt:
    request_id: str
    source_id: str
    url: str
    method: str
    attempt: int
    started_at: str
    finished_at: str
    status: int | None
    content_type: str | None
    response_sha256: str | None
    bytes_received: int
    truncated: bool
    records_extracted: int
    error_type: str | None = None
    error: str | None = None
    rate_limit: str | None = None
    rate_remaining: str | None = None
    retry_after: str | None = None
    raw_body_persisted: bool = False
    full_text_collected: bool = False

    @property
    def digest(self) -> str:
        return digest_object(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "digest": self.digest}


@dataclass(frozen=True)
class NegativeMemoryEntry:
    source_id: str
    kind: str
    detail: str
    request_id: str | None = None

    @property
    def digest(self) -> str:
        return digest_object(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "digest": self.digest}
