from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import re
from typing import Any, Mapping, Sequence

SHA256_PREFIX = "sha256:"
HMAC_SHA256_PREFIX = "hmac-sha256:"
VAULT_PREFIX = "vault://"

_SECRET_KEY_FRAGMENTS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "private_key",
        "access_token",
        "refresh_token",
        "api_key",
        "authorization",
        "cookie",
        "card_number",
        "bank_account",
        "routing_number",
        "social_insurance",
        "sin_number",
        "oauth",
    }
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9_]*-[0-9]{4}-[0-9]{4,12}$")


class CanonicalizationError(ValueError):
    """Raised when a value cannot safely enter a canonical public record."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return ensure_utc(value).isoformat().replace("+00:00", "Z")


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_casefold(value: str) -> str:
    return normalize_text(value).casefold()


def normalize_domain(value: str) -> str:
    domain = normalize_casefold(value).rstrip(".")
    if not _DOMAIN_RE.fullmatch(domain):
        raise CanonicalizationError(f"invalid domain: {value!r}")
    return domain


def normalize_email(value: str) -> str:
    email = normalize_casefold(value)
    if not _EMAIL_RE.fullmatch(email):
        raise CanonicalizationError("invalid email address")
    local, domain = email.rsplit("@", 1)
    return f"{local}@{normalize_domain(domain)}"


def validate_public_identifier(value: str, *, prefix: str | None = None) -> str:
    identifier = normalize_text(value).upper()
    if prefix and not identifier.startswith(prefix.upper() + "-"):
        raise CanonicalizationError(f"identifier must start with {prefix.upper()}-")
    if not _IDENTIFIER_RE.fullmatch(identifier):
        raise CanonicalizationError(
            "identifier must match PREFIX-YYYY-NUMBER using uppercase public-safe characters"
        )
    return identifier


def validate_vault_reference(value: str) -> str:
    reference = value.strip()
    if not reference.startswith(VAULT_PREFIX):
        raise CanonicalizationError("private references must use vault://")
    if " " in reference or ".." in reference:
        raise CanonicalizationError("invalid vault reference")
    if len(reference) > 512:
        raise CanonicalizationError("vault reference is too long")
    return reference


def _canonical_value(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical_value(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return isoformat_utc(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        normalized = [_canonical_value(item) for item in value]
        return sorted(normalized, key=lambda item: canonical_json(item))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            raise CanonicalizationError("non-finite floats are forbidden")
        return float(format(value, ".12g"))
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise CanonicalizationError(f"unsupported canonical value: {type(value).__name__}")


def canonical_mapping(value: Any) -> Any:
    return _canonical_value(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_mapping(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_bytes(value: bytes) -> str:
    return SHA256_PREFIX + hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_hash(value: Any) -> str:
    return sha256_text(canonical_json(value))


def hmac_identifier(secret: bytes, value: str, *, namespace: str) -> str:
    if len(secret) < 32:
        raise CanonicalizationError("HMAC secret must contain at least 32 bytes")
    normalized = f"{normalize_casefold(namespace)}\x00{normalize_casefold(value)}"
    digest = hmac.new(secret, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return HMAC_SHA256_PREFIX + digest


def is_sha256(value: str | None) -> bool:
    if value is None or not value.startswith(SHA256_PREFIX):
        return False
    digest = value[len(SHA256_PREFIX) :]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def is_hmac_sha256(value: str | None) -> bool:
    if value is None or not value.startswith(HMAC_SHA256_PREFIX):
        return False
    digest = value[len(HMAC_SHA256_PREFIX) :]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def assert_no_secret_keys(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).casefold().replace("-", "_")
            if any(fragment in normalized_key for fragment in _SECRET_KEY_FRAGMENTS):
                raise CanonicalizationError(f"secret-like key forbidden at {path}.{key}")
            assert_no_secret_keys(item, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            assert_no_secret_keys(item, path=f"{path}[{index}]")


def assert_public_safe_text(value: str, *, field: str, maximum: int = 4000) -> None:
    if len(value) > maximum:
        raise CanonicalizationError(f"{field} exceeds {maximum} characters")
    if "\r" in value or "\x00" in value:
        raise CanonicalizationError(f"{field} contains forbidden control characters")
    if _EMAIL_RE.search(value.strip()):
        raise CanonicalizationError(f"{field} must not contain a raw email address")


def stable_unique(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in seen:
            output.append(normalized)
            seen.add(normalized)
    return tuple(output)
