from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(payload: Any) -> str:
    raw = payload if isinstance(payload, str) else canonical_json(payload)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def stable_id(prefix: str, payload: Any, *, length: int = 20) -> str:
    return f"{prefix}-{sha256_hex(payload)[:length]}"
