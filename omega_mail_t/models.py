"""Typed models for Ω-MAIL-T."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_address(value: str) -> str:
    address = value.strip().lower()
    if address.count("@") != 1:
        raise ValueError(f"Invalid email address: {value!r}")
    local, domain = address.split("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError(f"Invalid email address: {value!r}")
    return address


def deterministic_id(*parts: object, prefix: str = "mail") -> str:
    payload = "\x1f".join(str(part) for part in parts)
    digest = sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


@dataclass(frozen=True, slots=True)
class Attachment:
    filename: str
    media_type: str = "application/octet-stream"
    content_sha256: str = "synthetic"
    size_bytes: int = 0
    synthetic: bool = True


@dataclass(slots=True)
class MailMessage:
    message_id: str
    thread_id: str
    sender: str
    recipients: tuple[str, ...]
    subject: str
    body: str
    intent: str
    language: str = "fr-CA"
    classification: str | None = None
    data_classification: str = "synthetic_internal"
    attachments: tuple[Attachment, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        self.sender = normalize_address(self.sender)
        self.recipients = tuple(normalize_address(value) for value in self.recipients)
        if not self.recipients:
            raise ValueError("A message must have at least one recipient")
        if not self.subject.strip():
            raise ValueError("A message subject cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Mailbox:
    address: str
    company_id: str
    role: str
    languages: tuple[str, ...] = ("fr-CA",)
    messages: list[MailMessage] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.address = normalize_address(self.address)

    def receive(self, message: MailMessage) -> None:
        self.messages.append(message)

    def latest(self) -> MailMessage | None:
        return self.messages[-1] if self.messages else None

    def thread(self, thread_id: str) -> list[MailMessage]:
        return [message for message in self.messages if message.thread_id == thread_id]


def recipients_tuple(values: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        return (normalize_address(values),)
    return tuple(normalize_address(value) for value in values)
