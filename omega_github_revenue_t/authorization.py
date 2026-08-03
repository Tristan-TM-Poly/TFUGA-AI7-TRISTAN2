from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class AuthorizationError(PermissionError):
    """Raised when an audit or external operation lacks explicit authorization."""


class Operation(str, Enum):
    READ_METADATA = "read_metadata"
    READ_TEXT = "read_text"
    COUNT_LINES = "count_lines"
    HASH_FILES = "hash_files"
    SCAN_RISK_PATTERNS = "scan_risk_patterns"
    GENERATE_REPORT = "generate_report"


@dataclass(frozen=True)
class AuditAuthorization:
    authorization_id: str
    repository_id: str
    granted_by: str
    granted_at: str
    operations: tuple[Operation, ...]
    explicitly_authorized: bool
    expires_at: str | None = None
    purpose: str = "bounded repository quality audit"
    data_classification: str = "public_or_owner_authorized"

    def validate(self, *, now: datetime | None = None) -> None:
        if not self.authorization_id.strip():
            raise AuthorizationError("authorization_id is required")
        if not self.repository_id.strip():
            raise AuthorizationError("repository_id is required")
        if not self.granted_by.strip():
            raise AuthorizationError("granted_by is required")
        if not self.explicitly_authorized:
            raise AuthorizationError("explicit authorization is required")
        if not self.operations:
            raise AuthorizationError("at least one authorized operation is required")
        granted = _parse_time(self.granted_at)
        current = now or datetime.now(timezone.utc)
        if granted > current:
            raise AuthorizationError("granted_at cannot be in the future")
        if self.expires_at is not None and _parse_time(self.expires_at) <= current:
            raise AuthorizationError("authorization has expired")

    def require(self, *operations: Operation) -> None:
        self.validate()
        missing = sorted(op.value for op in operations if op not in self.operations)
        if missing:
            raise AuthorizationError(f"missing authorized operations: {', '.join(missing)}")

    def to_public_receipt(self) -> dict[str, Any]:
        """Return a minimized receipt without private signatures or credentials."""
        self.validate()
        data = asdict(self)
        data["operations"] = [item.value for item in self.operations]
        return data


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AuthorizationError(f"invalid ISO-8601 time: {value}") from error
    if parsed.tzinfo is None:
        raise AuthorizationError("authorization times must include a timezone")
    return parsed.astimezone(timezone.utc)


def repository_identity(root: str | Path) -> str:
    path = Path(root).resolve()
    if not path.exists() or not path.is_dir():
        raise AuthorizationError(f"repository root does not exist: {path}")
    return path.name


def require_local_repository_match(root: str | Path, authorization: AuditAuthorization) -> Path:
    authorization.validate()
    path = Path(root).resolve()
    if not path.exists() or not path.is_dir():
        raise AuthorizationError(f"repository root does not exist: {path}")
    accepted = {path.name, str(path), path.as_posix()}
    if authorization.repository_id not in accepted:
        raise AuthorizationError(
            "authorization repository_id does not match the local audit target"
        )
    return path
