"""Append-only HMAC-authenticated receipts for reproducible campaigns.

HMAC receipts provide integrity and shared-secret authentication. They are not
public-key signatures, legal notarization, or proof that an external action
occurred.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Any, Iterable, Mapping

GENESIS = "sha256:" + "0" * 64


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True)
class AuthenticatedReceipt:
    sequence: int
    event: str
    payload_digest: str
    previous_digest: str
    chain_digest: str
    authentication: str
    scheme: str = "hmac-sha256-v1"


class ReceiptChain:
    def __init__(self, key: bytes, *, domain: str = "omega-re-r04") -> None:
        if not key:
            raise ValueError("HMAC key cannot be empty")
        self._key = bytes(key)
        self.domain = domain
        self._entries: list[AuthenticatedReceipt] = []

    @property
    def entries(self) -> tuple[AuthenticatedReceipt, ...]:
        return tuple(self._entries)

    def append(self, event: str, payload: Mapping[str, Any]) -> AuthenticatedReceipt:
        if not event.strip():
            raise ValueError("event cannot be blank")
        sequence = len(self._entries)
        previous = self._entries[-1].chain_digest if self._entries else GENESIS
        payload_digest = digest(payload)
        unsigned = {
            "domain": self.domain,
            "sequence": sequence,
            "event": event,
            "payload_digest": payload_digest,
            "previous_digest": previous,
        }
        chain_digest = digest(unsigned)
        authentication = "hmac-sha256:" + hmac.new(
            self._key,
            canonical_json(unsigned),
            hashlib.sha256,
        ).hexdigest()
        receipt = AuthenticatedReceipt(
            sequence=sequence,
            event=event,
            payload_digest=payload_digest,
            previous_digest=previous,
            chain_digest=chain_digest,
            authentication=authentication,
        )
        self._entries.append(receipt)
        return receipt

    def verify(self, entries: Iterable[AuthenticatedReceipt] | None = None) -> tuple[bool, tuple[str, ...]]:
        items = tuple(entries if entries is not None else self._entries)
        errors: list[str] = []
        previous = GENESIS
        for index, receipt in enumerate(items):
            if receipt.sequence != index:
                errors.append(f"sequence_mismatch:{index}")
            if receipt.previous_digest != previous:
                errors.append(f"previous_digest_mismatch:{index}")
            unsigned = {
                "domain": self.domain,
                "sequence": receipt.sequence,
                "event": receipt.event,
                "payload_digest": receipt.payload_digest,
                "previous_digest": receipt.previous_digest,
            }
            expected_chain = digest(unsigned)
            expected_auth = "hmac-sha256:" + hmac.new(
                self._key,
                canonical_json(unsigned),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(receipt.chain_digest, expected_chain):
                errors.append(f"chain_digest_mismatch:{index}")
            if not hmac.compare_digest(receipt.authentication, expected_auth):
                errors.append(f"authentication_mismatch:{index}")
            previous = receipt.chain_digest
        return not errors, tuple(errors)

    def export(self) -> list[dict[str, Any]]:
        return [asdict(entry) for entry in self._entries]
