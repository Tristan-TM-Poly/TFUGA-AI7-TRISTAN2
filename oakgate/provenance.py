"""Canonical SHA-256 provenance helpers for OAKGate claims."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .model import Claim


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def claim_provenance_hash(claim: Claim) -> str:
    payload = claim.to_dict(include_provenance=False)
    encoded = canonical_json(payload).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def verify_claim_provenance(claim: Claim) -> bool:
    if claim.provenance_hash is None:
        return True
    return claim.provenance_hash == claim_provenance_hash(claim)
