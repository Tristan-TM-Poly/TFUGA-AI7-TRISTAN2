"""Content-addressed research receipts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


GENESIS = "sha256:" + "0" * 64


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResearchReceipt:
    sequence: int
    previous_digest: str
    event_type: str
    payload: Mapping[str, Any]
    receipt_digest: str


def create_receipt(
    *,
    sequence: int,
    previous_digest: str,
    event_type: str,
    payload: Mapping[str, Any],
) -> ResearchReceipt:
    if sequence < 0:
        raise ValueError("sequence must be non-negative")
    if not event_type.strip():
        raise ValueError("event_type is empty")
    unsigned = {
        "sequence": sequence,
        "previous_digest": previous_digest,
        "event_type": event_type,
        "payload": dict(payload),
    }
    return ResearchReceipt(receipt_digest=sha256_digest(unsigned), **unsigned)


def verify_chain(receipts: Iterable[ResearchReceipt], *, genesis: str = GENESIS) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    previous = genesis
    for expected_sequence, receipt in enumerate(receipts):
        if receipt.sequence != expected_sequence:
            errors.append(f"sequence mismatch at {expected_sequence}: {receipt.sequence}")
        if receipt.previous_digest != previous:
            errors.append(f"previous digest mismatch at {expected_sequence}")
        expected = create_receipt(
            sequence=receipt.sequence,
            previous_digest=receipt.previous_digest,
            event_type=receipt.event_type,
            payload=receipt.payload,
        ).receipt_digest
        if expected != receipt.receipt_digest:
            errors.append(f"receipt digest mismatch at {expected_sequence}")
        previous = receipt.receipt_digest
    return not errors, tuple(errors)


def chain_to_json(receipts: Iterable[ResearchReceipt]) -> str:
    return json.dumps([asdict(item) for item in receipts], ensure_ascii=False, sort_keys=True, indent=2) + "\n"
