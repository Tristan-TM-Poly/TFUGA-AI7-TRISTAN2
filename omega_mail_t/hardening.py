"""Execution-time hardening for one-message official mail.

The ledger stores hashes and operational state only. It does not store message
subjects, bodies, credentials, legal evidence, or plaintext recipients.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

from .officialization import ApprovalRecord, OfficialMessageDraft

MAX_SUBJECT_CHARS = 200
MAX_BODY_BYTES = 256_000
MAX_APPROVAL_AGE_SECONDS = 3_600
MAX_APPROVAL_AGE_LIMIT_SECONDS = 86_400
CLOCK_SKEW_SECONDS = 300
GENESIS_HASH = "sha256:" + "0" * 64


def _utc_now(now: datetime | None = None) -> datetime:
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc)


def _iso(instant: datetime) -> str:
    return _utc_now(instant).isoformat().replace("+00:00", "Z")


def _parse_instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def recipient_hash(address: str) -> str:
    return _sha256_text(address.strip().casefold())


def validate_delivery_draft(draft: OfficialMessageDraft) -> tuple[str, ...]:
    """Return deterministic blockers for a delivery attempt."""
    reasons: list[str] = []
    if len(draft.recipients) != 1:
        reasons.append("delivery_requires_exactly_one_recipient")
    if draft.attachments:
        reasons.append("attachments_require_content_addressed_pipeline")
    if "\r" in draft.subject or "\n" in draft.subject:
        reasons.append("subject_header_injection_detected")
    if len(draft.subject) > MAX_SUBJECT_CHARS:
        reasons.append("subject_too_long")
    if len(draft.body.encode("utf-8")) > MAX_BODY_BYTES:
        reasons.append("body_too_large")
    if "\r" in draft.sender or "\n" in draft.sender:
        reasons.append("sender_header_injection_detected")
    if any("\r" in value or "\n" in value for value in draft.recipients):
        reasons.append("recipient_header_injection_detected")
    return tuple(reasons)


def validate_approval_for_execution(
    approval: ApprovalRecord | None,
    draft: OfficialMessageDraft,
    *,
    now: datetime | None = None,
    max_age_seconds: int = MAX_APPROVAL_AGE_SECONDS,
) -> tuple[str, ...]:
    """Validate exact approval binding and execution-time freshness."""
    reasons: list[str] = []
    if approval is None:
        return ("execution_approval_missing",)
    if approval.message_hash != draft.content_hash:
        reasons.append("execution_approval_hash_mismatch")
    if approval.scope != "ONE_MESSAGE":
        reasons.append("execution_approval_scope_invalid")
    if not approval.approver.strip():
        reasons.append("execution_approver_missing")
    if not 1 <= max_age_seconds <= MAX_APPROVAL_AGE_LIMIT_SECONDS:
        reasons.append("approval_age_policy_out_of_bounds")
        return tuple(reasons)
    try:
        approved = _parse_instant(approval.approved_at)
    except (TypeError, ValueError):
        reasons.append("execution_approval_time_invalid")
        return tuple(reasons)
    age = (_utc_now(now) - approved).total_seconds()
    if age < -CLOCK_SKEW_SECONDS:
        reasons.append("execution_approval_from_future")
    elif age > max_age_seconds:
        reasons.append("execution_approval_expired")
    return tuple(reasons)


@dataclass(frozen=True, slots=True)
class LedgerReservation:
    reservation_id: str
    entry_hash: str
    message_hash: str
    recipient_hash: str


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    event: str
    message_hash: str
    recipient_hash: str
    provider: str
    occurred_at: str
    reservation_id: str
    previous_hash: str
    detail: str
    entry_hash: str

    def payload_without_hash(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("entry_hash")
        return payload

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "LedgerEntry":
        return cls(
            sequence=int(data["sequence"]),
            event=str(data["event"]),
            message_hash=str(data["message_hash"]),
            recipient_hash=str(data["recipient_hash"]),
            provider=str(data["provider"]),
            occurred_at=str(data["occurred_at"]),
            reservation_id=str(data["reservation_id"]),
            previous_hash=str(data["previous_hash"]),
            detail=str(data.get("detail", "")),
            entry_hash=str(data["entry_hash"]),
        )


def _entry_digest(payload: Mapping[str, Any]) -> str:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_text(rendered)


class OneMessageLedger:
    """Append-only, hash-chained execution ledger with a coarse file lock."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                self.lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as exc:
            raise RuntimeError("execution ledger is locked by another process") from exc
        try:
            os.write(descriptor, f"pid={os.getpid()}\n".encode("utf-8"))
            yield
        finally:
            os.close(descriptor)
            self.lock_path.unlink(missing_ok=True)

    def entries(self) -> tuple[LedgerEntry, ...]:
        if not self.path.exists():
            return ()
        entries: list[LedgerEntry] = []
        previous = GENESIS_HASH
        for expected_sequence, raw in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not raw.strip():
                continue
            try:
                entry = LedgerEntry.from_mapping(json.loads(raw))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("execution ledger contains a malformed entry") from exc
            if entry.sequence != expected_sequence:
                raise RuntimeError("execution ledger sequence mismatch")
            if entry.previous_hash != previous:
                raise RuntimeError("execution ledger hash-chain mismatch")
            if _entry_digest(entry.payload_without_hash()) != entry.entry_hash:
                raise RuntimeError("execution ledger entry hash mismatch")
            entries.append(entry)
            previous = entry.entry_hash
        return tuple(entries)

    def _append(
        self,
        *,
        event: str,
        message_hash: str,
        recipient_digest: str,
        provider: str,
        occurred_at: datetime,
        reservation_id: str,
        detail: str = "",
    ) -> LedgerEntry:
        entries = self.entries()
        previous = entries[-1].entry_hash if entries else GENESIS_HASH
        payload = {
            "sequence": len(entries) + 1,
            "event": event,
            "message_hash": message_hash,
            "recipient_hash": recipient_digest,
            "provider": provider,
            "occurred_at": _iso(occurred_at),
            "reservation_id": reservation_id,
            "previous_hash": previous,
            "detail": detail,
        }
        entry = LedgerEntry(entry_hash=_entry_digest(payload), **payload)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry.to_mapping(), ensure_ascii=False, sort_keys=True))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return entry

    def reserve(
        self,
        draft: OfficialMessageDraft,
        *,
        provider: str,
        now: datetime | None = None,
    ) -> LedgerReservation:
        instant = _utc_now(now)
        recipient = draft.recipients[0] if draft.recipients else ""
        recipient_digest = recipient_hash(recipient)
        with self._locked():
            entries = self.entries()
            if any(
                entry.message_hash == draft.content_hash
                and entry.event in {"RESERVED", "ACCEPTED_BY_PROVIDER", "DELIVERED"}
                for entry in entries
            ):
                raise RuntimeError("message hash is already reserved or consumed")
            seed = ":".join(
                (
                    draft.content_hash,
                    recipient_digest,
                    provider,
                    _iso(instant),
                    str(len(entries) + 1),
                )
            )
            reservation_id = _sha256_text(seed)
            entry = self._append(
                event="RESERVED",
                message_hash=draft.content_hash,
                recipient_digest=recipient_digest,
                provider=provider,
                occurred_at=instant,
                reservation_id=reservation_id,
                detail="reserved_before_network_attempt",
            )
        return LedgerReservation(
            reservation_id=reservation_id,
            entry_hash=entry.entry_hash,
            message_hash=draft.content_hash,
            recipient_hash=recipient_digest,
        )

    def record_result(
        self,
        reservation: LedgerReservation,
        *,
        provider: str,
        event: str,
        detail: str = "",
        now: datetime | None = None,
    ) -> LedgerEntry:
        with self._locked():
            entries = self.entries()
            if not any(
                entry.reservation_id == reservation.reservation_id
                and entry.event == "RESERVED"
                for entry in entries
            ):
                raise RuntimeError("unknown ledger reservation")
            return self._append(
                event=event,
                message_hash=reservation.message_hash,
                recipient_digest=reservation.recipient_hash,
                provider=provider,
                occurred_at=_utc_now(now),
                reservation_id=reservation.reservation_id,
                detail=detail,
            )

    def audit(self) -> dict[str, Any]:
        entries = self.entries()
        return {
            "entries": len(entries),
            "reservations": sum(entry.event == "RESERVED" for entry in entries),
            "accepted": sum(entry.event == "ACCEPTED_BY_PROVIDER" for entry in entries),
            "errors": sum(entry.event == "SEND_ERROR" for entry in entries),
            "head_hash": entries[-1].entry_hash if entries else GENESIS_HASH,
            "stores_plaintext_recipient": False,
            "stores_message_content": False,
        }
