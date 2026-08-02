"""Parse bounded OMEGA-GITHUB command blocks from email text."""
from __future__ import annotations

from hashlib import sha256
import re
from typing import Iterable

from .models import MailCommand

_BLOCK_RE = re.compile(r"OMEGA-GITHUB:\s*(.*?)(?:\n\s*\n|\Z)", re.IGNORECASE | re.DOTALL)
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_KEYS = {"repo", "action", "target", "objective", "required", "authority", "base_branch"}


class CommandParseError(ValueError):
    pass


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"yes", "true", "1", "oui"}:
        return True
    if normalized in {"no", "false", "0", "non"}:
        return False
    raise CommandParseError(f"invalid_boolean:{value}")


def _lines(text: str) -> Iterable[str]:
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            yield line.rstrip()


def parse_command(text: str, *, message_id: str | None = None, thread_id: str | None = None, sender: str | None = None) -> MailCommand:
    match = _BLOCK_RE.search(text)
    if not match:
        raise CommandParseError("missing_omega_github_block")
    data: dict[str, object] = {"required": [], "authority": {}}
    section: str | None = None
    for raw in _lines(match.group(1)):
        stripped = raw.strip()
        if stripped.startswith("-"):
            if section != "required":
                raise CommandParseError("list_item_outside_required")
            required = data.setdefault("required", [])
            assert isinstance(required, list)
            required.append(stripped[1:].strip())
            continue
        if ":" not in stripped:
            raise CommandParseError(f"invalid_line:{stripped}")
        key, value = (part.strip() for part in stripped.split(":", 1))
        key = key.lower()
        if key not in _ALLOWED_KEYS and section != "authority":
            raise CommandParseError(f"unknown_key:{key}")
        if raw.startswith((" ", "\t")) and section == "authority":
            authority = data.setdefault("authority", {})
            assert isinstance(authority, dict)
            authority[key] = _as_bool(value)
            continue
        if key in {"required", "authority"} and value == "":
            section = key
            continue
        section = None
        data[key] = value
    missing = [key for key in ("repo", "action", "target", "objective") if not data.get(key)]
    if missing:
        raise CommandParseError("missing_required_fields:" + ",".join(missing))
    repository = str(data["repo"])
    if not _REPO_RE.fullmatch(repository):
        raise CommandParseError("invalid_repository")
    target = str(data["target"])
    if target.startswith("/") or ".." in target.split("/"):
        raise CommandParseError("unsafe_target_path")
    return MailCommand(
        repository=repository,
        action=str(data["action"]),
        target=target,
        objective=str(data["objective"]),
        required=tuple(str(item) for item in data.get("required", [])),
        authority={str(k): bool(v) for k, v in dict(data.get("authority", {})).items()},
        base_branch=str(data.get("base_branch") or "main"),
        message_id=message_id,
        thread_id=thread_id,
        sender=sender,
        raw_hash=sha256(text.encode("utf-8")).hexdigest(),
    )
