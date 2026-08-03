from __future__ import annotations

from dataclasses import replace

from .hashing import sha256_hex
from .models import CampaignReceipt


def sign_receipt(receipt: CampaignReceipt) -> CampaignReceipt:
    digest = sha256_hex(receipt.to_dict(include_hash=False))
    return replace(receipt, receipt_sha256=digest)


def verify_receipt(receipt: CampaignReceipt) -> bool:
    return receipt.receipt_sha256 == sha256_hex(receipt.to_dict(include_hash=False))


def verify_receipt_dict(payload: dict[str, object]) -> bool:
    expected = payload.get("receipt_sha256")
    if not isinstance(expected, str):
        return False
    unsigned = dict(payload)
    unsigned.pop("receipt_sha256", None)
    return expected == sha256_hex(unsigned)
