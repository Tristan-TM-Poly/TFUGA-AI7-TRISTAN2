"""Publicly verifiable Lamport one-time receipts using SHA-256 only.

This educational implementation is deterministic for tests and portable across
Python versions.  A Lamport key must sign at most one message.  It is not a
replacement for reviewed modern signature libraries, PKI, timestamping, or
legal notarization.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Sequence

BITS = 256


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def digest_hex(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def _derive(seed: bytes, index: int, bit: int) -> bytes:
    return sha256(seed + index.to_bytes(2, "big") + bytes([bit]))


@dataclass(frozen=True)
class LamportPublicKey:
    commitments: tuple[tuple[str, str], ...]
    key_id: str
    scheme: str = "lamport-sha256-one-time-v1"


@dataclass(frozen=True)
class LamportPrivateKey:
    secrets: tuple[tuple[bytes, bytes], ...]
    public_key: LamportPublicKey


@dataclass(frozen=True)
class PublicReceipt:
    domain: str
    sequence: int
    previous_digest: str
    payload_digest: str
    receipt_digest: str
    public_key: LamportPublicKey
    signature: tuple[str, ...]
    claim: str = "public_integrity_receipt_only"


def generate_keypair(seed: bytes) -> LamportPrivateKey:
    if len(seed) < 16:
        raise ValueError("seed must contain at least 16 bytes")
    secrets = tuple((_derive(seed, index, 0), _derive(seed, index, 1)) for index in range(BITS))
    commitments = tuple((sha256(zero).hex(), sha256(one).hex()) for zero, one in secrets)
    key_id = digest_hex({"commitments": commitments})
    public = LamportPublicKey(commitments=commitments, key_id=key_id)
    return LamportPrivateKey(secrets=secrets, public_key=public)


def _message_bits(message: bytes) -> tuple[int, ...]:
    digest = sha256(message)
    return tuple((byte >> shift) & 1 for byte in digest for shift in range(7, -1, -1))


def sign(message: bytes, private_key: LamportPrivateKey) -> tuple[str, ...]:
    bits = _message_bits(message)
    return tuple(private_key.secrets[index][bit].hex() for index, bit in enumerate(bits))


def verify(message: bytes, signature: Sequence[str], public_key: LamportPublicKey) -> bool:
    if len(signature) != BITS or len(public_key.commitments) != BITS:
        return False
    bits = _message_bits(message)
    try:
        return all(
            hashlib.sha256(bytes.fromhex(signature[index])).hexdigest()
            == public_key.commitments[index][bit]
            for index, bit in enumerate(bits)
        )
    except ValueError:
        return False


def create_receipt(
    *,
    domain: str,
    sequence: int,
    previous_digest: str,
    payload: Any,
    private_key: LamportPrivateKey,
) -> PublicReceipt:
    if not domain.strip() or sequence < 0:
        raise ValueError("invalid receipt identity")
    unsigned = {
        "domain": domain,
        "sequence": sequence,
        "previous_digest": previous_digest,
        "payload_digest": digest_hex(payload),
        "public_key_id": private_key.public_key.key_id,
    }
    message = canonical_json(unsigned)
    return PublicReceipt(
        domain=domain,
        sequence=sequence,
        previous_digest=previous_digest,
        payload_digest=unsigned["payload_digest"],
        receipt_digest=digest_hex(unsigned),
        public_key=private_key.public_key,
        signature=sign(message, private_key),
    )


def verify_receipt(receipt: PublicReceipt) -> bool:
    unsigned = {
        "domain": receipt.domain,
        "sequence": receipt.sequence,
        "previous_digest": receipt.previous_digest,
        "payload_digest": receipt.payload_digest,
        "public_key_id": receipt.public_key.key_id,
    }
    return receipt.receipt_digest == digest_hex(unsigned) and verify(
        canonical_json(unsigned), receipt.signature, receipt.public_key
    )


def verify_chain(receipts: Iterable[PublicReceipt], *, genesis: str = "sha256:" + "0" * 64) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    previous = genesis
    seen_keys: set[str] = set()
    for index, receipt in enumerate(receipts):
        if receipt.sequence != index:
            errors.append(f"sequence:{index}")
        if receipt.previous_digest != previous:
            errors.append(f"previous:{index}")
        if receipt.public_key.key_id in seen_keys:
            errors.append(f"one_time_key_reuse:{index}")
        if not verify_receipt(receipt):
            errors.append(f"signature:{index}")
        seen_keys.add(receipt.public_key.key_id)
        previous = receipt.receipt_digest
    return not errors, tuple(errors)
