"""Security, idempotence, and anti-loop primitives."""
from __future__ import annotations

import hashlib
import json
import re
from email.utils import parseaddr
from typing import Any

INJECTION_PATTERNS = (
    r"ignore (all|any|the) (previous|prior|system) instructions",
    r"reveal (the )?(system prompt|secrets?|credentials?)",
    r"upload all (data|files|documents)",
    r"disable (safety|security|oak|policy)",
    r"bypass (approval|authorization|policy)",
)

AUTO_RESPONSE_HEADERS = {
    "auto-submitted",
    "x-autoreply",
    "x-autorespond",
    "precedence",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_address(address: str) -> str:
    _, parsed = parseaddr(address)
    parsed = parsed.strip().lower()
    if "@" not in parsed:
        raise ValueError(f"invalid email address: {address!r}")
    return parsed


def scan_untrusted_text(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    findings = [f"prompt_injection_pattern:{pattern}" for pattern in INJECTION_PATTERNS if re.search(pattern, lowered)]
    return tuple(findings)


def is_auto_generated(headers: dict[str, str], sender: str, owned_addresses: set[str]) -> bool:
    normalized = {key.lower(): str(value).lower() for key, value in headers.items()}
    if normalize_address(sender) in {normalize_address(item) for item in owned_addresses}:
        return True
    if normalized.get("auto-submitted", "no") not in {"", "no"}:
        return True
    if normalized.get("x-autoreply") or normalized.get("x-autorespond"):
        return True
    if normalized.get("precedence") in {"bulk", "junk", "list"}:
        return True
    return False


def idempotency_key(provider: str, external_id: str, raw_hash: str) -> str:
    return sha256_value({"provider": provider, "external_id": external_id, "raw_hash": raw_hash})
