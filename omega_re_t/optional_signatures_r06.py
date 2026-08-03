"""Optional Ed25519 adapter with fail-closed dependency and key handling.

No private key material is generated from deterministic seeds in production mode.
The module requires the external ``cryptography`` package for Ed25519 operations.
"""
from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
from typing import Callable


@dataclass(frozen=True)
class SignatureEnvelope:
    algorithm: str
    public_key_b64: str
    signature_b64: str
    message_digest: str
    key_id: str
    claim: str = "cryptographic_integrity_only"


def backend_available() -> bool:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: F401
    except Exception:
        return False
    return True


def _require_backend():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    except Exception as exc:
        raise RuntimeError("Ed25519 backend unavailable; install the audited optional dependency") from exc
    return serialization, Ed25519PrivateKey, Ed25519PublicKey


def generate_keypair(*, allow_generation: bool = False) -> tuple[bytes, bytes]:
    if not allow_generation:
        raise PermissionError("key generation requires explicit allow_generation=True")
    serialization, private_type, _ = _require_backend()
    private = private_type.generate()
    public = private.public_key()
    private_raw = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return private_raw, public_raw


def sign_message(message: bytes, private_key_raw: bytes) -> SignatureEnvelope:
    serialization, private_type, _ = _require_backend()
    del serialization
    if len(private_key_raw) != 32:
        raise ValueError("Ed25519 private key must be 32 raw bytes")
    private = private_type.from_private_bytes(private_key_raw)
    public = private.public_key()
    from cryptography.hazmat.primitives import serialization as ser
    public_raw = public.public_bytes(encoding=ser.Encoding.Raw, format=ser.PublicFormat.Raw)
    signature = private.sign(message)
    message_digest = "sha256:" + hashlib.sha256(message).hexdigest()
    key_id = "sha256:" + hashlib.sha256(public_raw).hexdigest()
    return SignatureEnvelope(
        algorithm="ed25519",
        public_key_b64=base64.b64encode(public_raw).decode(),
        signature_b64=base64.b64encode(signature).decode(),
        message_digest=message_digest,
        key_id=key_id,
    )


def verify_message(message: bytes, envelope: SignatureEnvelope) -> bool:
    _, _, public_type = _require_backend()
    if envelope.algorithm != "ed25519":
        return False
    public_raw = base64.b64decode(envelope.public_key_b64, validate=True)
    signature = base64.b64decode(envelope.signature_b64, validate=True)
    expected_digest = "sha256:" + hashlib.sha256(message).hexdigest()
    expected_key_id = "sha256:" + hashlib.sha256(public_raw).hexdigest()
    if expected_digest != envelope.message_digest or expected_key_id != envelope.key_id:
        return False
    try:
        public_type.from_public_bytes(public_raw).verify(signature, message)
    except Exception:
        return False
    return True


def fail_closed_operation(operation: Callable[[], object]) -> object:
    if not backend_available():
        raise RuntimeError("optional signature backend unavailable")
    return operation()
