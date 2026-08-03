from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class SensitiveDataError(ValueError):
    """Raised when a payload contains fields forbidden from repository ledgers."""


_FORBIDDEN_KEYS = {
    "account_number",
    "bank_account",
    "bank_account_number",
    "void_cheque",
    "transit",
    "transit_number",
    "institution_number",
    "routing_number",
    "swift",
    "iban",
    "sin",
    "social_insurance_number",
    "tax_id",
    "home_address",
    "stripe_secret",
    "api_key",
    "password",
    "credential",
}


def _normalized_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def reject_sensitive_fields(payload: Any, *, path: str = "$") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized = _normalized_key(str(key))
            if normalized in _FORBIDDEN_KEYS:
                raise SensitiveDataError(f"forbidden sensitive field at {path}.{key}")
            reject_sensitive_fields(value, path=f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            reject_sensitive_fields(value, path=f"{path}[{index}]")


def canonical_json(payload: Mapping[str, Any]) -> str:
    reject_sensitive_fields(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class AppendOnlyLedger:
    """Hash-chained JSONL ledger.

    The ledger is an integrity aid, not a bank statement, tax return, legal receipt,
    blockchain, or substitute for provider reconciliation.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        last = ""
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = line
        if not last:
            return "0" * 64
        record = json.loads(last)
        return str(record["record_hash"])

    def append(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        reject_sensitive_fields(payload)
        previous_hash = self._last_hash()
        body = {"previous_hash": previous_hash, "payload": dict(payload)}
        record_hash = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
        record = body | {"record_hash": record_hash}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def verify(self) -> tuple[bool, int, str | None]:
        if not self.path.exists():
            return True, 0, None
        expected_previous = "0" * 64
        count = 0
        with self.path.open("r", encoding="utf-8") as handle:
            for count, line in enumerate(handle, start=1):
                record = json.loads(line)
                if record.get("previous_hash") != expected_previous:
                    return False, count, "previous hash mismatch"
                payload = record.get("payload")
                reject_sensitive_fields(payload)
                body = {"previous_hash": expected_previous, "payload": payload}
                expected_hash = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
                if record.get("record_hash") != expected_hash:
                    return False, count, "record hash mismatch"
                expected_previous = expected_hash
        return True, count, None
