from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 16) -> str:
    if length <= 0 or length > 64:
        raise ValueError("length must be in [1, 64]")
    return f"{prefix}-{sha256_hex(payload)[:length]}"
