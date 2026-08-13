from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .core import TransformationReceipt, stable_digest
from .receipts import ReceiptError, validate_receipt

GENESIS_HASH = "GENESIS"


@dataclass(frozen=True)
class TransitionLedgerEntry:
    index: int
    previous_hash: str
    receipt_id: str
    receipt_fingerprint: str
    state_before: str
    state_after: str
    chain_hash: str

    def body(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "receipt_id": self.receipt_id,
            "receipt_fingerprint": self.receipt_fingerprint,
            "state_before": self.state_before,
            "state_after": self.state_after,
        }


class ResearchTransitionLedger:
    """Append-only-by-contract hash chain for transformation receipts.

    The Python list is not a security boundary. `verify()` detects accidental or
    deliberate in-memory/history mutation relative to the recorded hash chain;
    it does not replace signed commits, external timestamps or independent audit.
    """

    def __init__(self) -> None:
        self.entries: list[TransitionLedgerEntry] = []

    def append(
        self,
        receipt: TransformationReceipt,
        *,
        state_before: str,
        state_after: str,
    ) -> TransitionLedgerEntry:
        validation = validate_receipt(receipt)
        if validation["status"] != "PASS":
            raise ReceiptError(f"cannot append invalid receipt: {validation['errors']}")
        if not state_before or not state_after:
            raise ValueError("state_before and state_after fingerprints are required")
        previous = self.entries[-1].chain_hash if self.entries else GENESIS_HASH
        body = {
            "index": len(self.entries),
            "previous_hash": previous,
            "receipt_id": receipt.receipt_id,
            "receipt_fingerprint": receipt.fingerprint,
            "state_before": state_before,
            "state_after": state_after,
        }
        entry = TransitionLedgerEntry(chain_hash=stable_digest(body), **body)
        self.entries.append(entry)
        return entry

    @property
    def head_hash(self) -> str:
        return self.entries[-1].chain_hash if self.entries else GENESIS_HASH

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        previous = GENESIS_HASH
        expected_state: str | None = None
        for expected_index, entry in enumerate(self.entries):
            if entry.index != expected_index:
                errors.append(f"entry {expected_index}: index mismatch {entry.index}")
            if entry.previous_hash != previous:
                errors.append(f"entry {expected_index}: previous hash mismatch")
            if expected_state is not None and entry.state_before != expected_state:
                errors.append(f"entry {expected_index}: state continuity mismatch")
            recomputed = stable_digest(entry.body())
            if entry.chain_hash != recomputed:
                errors.append(f"entry {expected_index}: chain hash mismatch")
            previous = entry.chain_hash
            expected_state = entry.state_after
        payload = {
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
            "entry_count": len(self.entries),
            "head_hash": self.head_hash,
        }
        payload["fingerprint"] = stable_digest(payload)
        return payload

    def trace_state(self, state_hash: str) -> tuple[TransitionLedgerEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.state_before == state_hash or entry.state_after == state_hash
        )

    def to_dict(self) -> dict[str, Any]:
        verification = self.verify()
        return {
            "schema": "omega-research-transition-ledger/v0.2.0",
            "entries": [asdict(entry) for entry in self.entries],
            "verification": verification,
            "boundary": (
                "hash_chain_integrity != external_truth_or_signature; "
                "receipt_validity != semantic_correctness"
            ),
        }
