"""One-message production connector with explicit, layered operator locks."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from email.message import EmailMessage
import os
import smtplib
import ssl
from typing import Protocol

from .hardening import (
    MAX_APPROVAL_AGE_SECONDS,
    MAX_APPROVAL_AGE_LIMIT_SECONDS,
    OneMessageLedger,
    validate_approval_for_execution,
    validate_delivery_draft,
)
from .officialization import (
    ApprovalRecord,
    OfficialDecision,
    OfficialGateReport,
    OfficialMessageDraft,
)


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    provider: str
    status: str
    message_hash: str
    recipient: str
    provider_message_id: str | None = None
    detail: str = ""
    reservation_id: str | None = None
    ledger_entry_hash: str | None = None

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "status": self.status,
            "message_hash": self.message_hash,
            "recipient": self.recipient,
            "provider_message_id": self.provider_message_id,
            "detail": self.detail,
            "reservation_id": self.reservation_id,
            "ledger_entry_hash": self.ledger_entry_hash,
        }


class MailProvider(Protocol):
    name: str

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
        ...


class DryRunProvider:
    name = "dry-run"

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
        blockers = validate_delivery_draft(draft)
        if blockers:
            raise RuntimeError("delivery draft blocked: " + ",".join(blockers))
        recipient = draft.recipients[0] if draft.recipients else ""
        return DeliveryReceipt(
            provider=self.name,
            status="DRY_RUN",
            message_hash=draft.content_hash,
            recipient=recipient,
            detail="No network connection was opened and no email was sent.",
        )


@dataclass(frozen=True, slots=True)
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True
    starttls: bool = False
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "SMTPConfig":
        required = {
            "OMEGA_MAIL_SMTP_HOST": os.getenv("OMEGA_MAIL_SMTP_HOST"),
            "OMEGA_MAIL_SMTP_USERNAME": os.getenv("OMEGA_MAIL_SMTP_USERNAME"),
            "OMEGA_MAIL_SMTP_PASSWORD": os.getenv("OMEGA_MAIL_SMTP_PASSWORD"),
        }
        missing = sorted(name for name, value in required.items() if not value)
        if missing:
            raise RuntimeError("missing SMTP environment variables: " + ",".join(missing))
        return cls(
            host=required["OMEGA_MAIL_SMTP_HOST"] or "",
            port=int(os.getenv("OMEGA_MAIL_SMTP_PORT", "465")),
            username=required["OMEGA_MAIL_SMTP_USERNAME"] or "",
            password=required["OMEGA_MAIL_SMTP_PASSWORD"] or "",
            use_ssl=os.getenv("OMEGA_MAIL_SMTP_SSL", "1") == "1",
            starttls=os.getenv("OMEGA_MAIL_SMTP_STARTTLS", "0") == "1",
            timeout_seconds=float(os.getenv("OMEGA_MAIL_SMTP_TIMEOUT", "30")),
        )

    def validate_transport(self) -> None:
        if self.use_ssl == self.starttls:
            raise RuntimeError("exactly one of SMTP SSL or STARTTLS must be enabled")
        if not 1 <= self.port <= 65535:
            raise RuntimeError("SMTP port is out of range")
        if not 1 <= self.timeout_seconds <= 120:
            raise RuntimeError("SMTP timeout is out of bounds")
        allowed_host = (os.getenv("OMEGA_MAIL_ALLOWED_SMTP_HOST") or "").strip().casefold()
        if not allowed_host or self.host.strip().casefold() != allowed_host:
            raise RuntimeError("SMTP host does not match OMEGA_MAIL_ALLOWED_SMTP_HOST")
        allowed_port = (os.getenv("OMEGA_MAIL_ALLOWED_SMTP_PORT") or "").strip()
        if not allowed_port or str(self.port) != allowed_port:
            raise RuntimeError("SMTP port does not match OMEGA_MAIL_ALLOWED_SMTP_PORT")


def render_message(draft: OfficialMessageDraft) -> EmailMessage:
    """Render deterministic approved headers and plaintext body."""
    blockers = validate_delivery_draft(draft)
    if blockers:
        raise RuntimeError("delivery draft blocked: " + ",".join(blockers))
    recipient = draft.recipients[0]
    domain = draft.sender.rsplit("@", 1)[1]
    digest = draft.content_hash.removeprefix("sha256:")
    message = EmailMessage()
    message["From"] = draft.sender
    message["To"] = recipient
    message["Subject"] = draft.subject
    message["Message-ID"] = f"<omega-{digest[:32]}@{domain}>"
    message.set_content(draft.body)
    return message


class SMTPProvider:
    """SMTP provider limited to one pre-approved recipient per invocation."""

    name = "smtp"

    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
        if os.getenv("OMEGA_MAIL_EXTERNAL_SEND") != "I_ACKNOWLEDGE_ONE_MESSAGE":
            raise RuntimeError("external-send acknowledgement is absent")
        self.config.validate_transport()
        if len(draft.recipients) != 1:
            raise RuntimeError("SMTPProvider permits exactly one recipient")
        recipient = draft.recipients[0]
        allowlisted = (os.getenv("OMEGA_MAIL_ALLOWED_RECIPIENT") or "").strip().casefold()
        if not allowlisted or recipient.casefold() != allowlisted:
            raise RuntimeError("recipient does not match OMEGA_MAIL_ALLOWED_RECIPIENT")

        message = render_message(draft)
        context = ssl.create_default_context()
        if self.config.use_ssl:
            with smtplib.SMTP_SSL(
                self.config.host,
                self.config.port,
                timeout=self.config.timeout_seconds,
                context=context,
            ) as client:
                client.login(self.config.username, self.config.password)
                client.send_message(message)
        else:
            with smtplib.SMTP(
                self.config.host,
                self.config.port,
                timeout=self.config.timeout_seconds,
            ) as client:
                client.starttls(context=context)
                client.login(self.config.username, self.config.password)
                client.send_message(message)

        return DeliveryReceipt(
            provider=self.name,
            status="ACCEPTED_BY_PROVIDER",
            message_hash=draft.content_hash,
            recipient=recipient,
            provider_message_id=str(message["Message-ID"]),
            detail="Provider acceptance is not proof of final delivery.",
        )


def _approval_max_age_seconds() -> int:
    raw = os.getenv("OMEGA_MAIL_APPROVAL_MAX_AGE_SECONDS")
    if raw is None:
        return MAX_APPROVAL_AGE_SECONDS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("OMEGA_MAIL_APPROVAL_MAX_AGE_SECONDS must be an integer") from exc
    if not 1 <= value <= MAX_APPROVAL_AGE_LIMIT_SECONDS:
        raise RuntimeError("approval max age must be between 1 and 86400 seconds")
    return value


def _execution_ledger(ledger: OneMessageLedger | None) -> OneMessageLedger:
    if ledger is not None:
        return ledger
    path = (os.getenv("OMEGA_MAIL_EXECUTION_LEDGER") or "").strip()
    if not path:
        raise RuntimeError("OMEGA_MAIL_EXECUTION_LEDGER is required for execution")
    return OneMessageLedger(path)


def deliver_one(
    *,
    report: OfficialGateReport,
    draft: OfficialMessageDraft,
    execute: bool = False,
    provider: MailProvider | None = None,
    approval: ApprovalRecord | None = None,
    ledger: OneMessageLedger | None = None,
    now: datetime | None = None,
) -> DeliveryReceipt:
    """Deliver one message, or produce a no-network dry-run receipt."""
    blockers = validate_delivery_draft(draft)
    if blockers:
        raise RuntimeError("delivery draft blocked: " + ",".join(blockers))

    if execute:
        if report.decision != OfficialDecision.ALLOW_ONE_MESSAGE:
            raise RuntimeError(f"production gate denied send: {report.decision.value}")
        approval_blockers = validate_approval_for_execution(
            approval,
            draft,
            now=now,
            max_age_seconds=_approval_max_age_seconds(),
        )
        if approval_blockers:
            raise RuntimeError("execution approval blocked: " + ",".join(approval_blockers))
        selected = provider or SMTPProvider(SMTPConfig.from_env())
        execution_ledger = _execution_ledger(ledger)
        reservation = execution_ledger.reserve(draft, provider=selected.name, now=now)
        try:
            receipt = selected.send(draft)
        except Exception as exc:
            try:
                execution_ledger.record_result(
                    reservation,
                    provider=selected.name,
                    event="SEND_ERROR",
                    detail=type(exc).__name__,
                    now=now,
                )
            finally:
                raise
        result_entry = execution_ledger.record_result(
            reservation,
            provider=selected.name,
            event=receipt.status,
            detail="provider_result_recorded",
            now=now,
        )
        return replace(
            receipt,
            reservation_id=reservation.reservation_id,
            ledger_entry_hash=result_entry.entry_hash,
        )

    if report.decision not in {
        OfficialDecision.ALLOW_DRY_RUN,
        OfficialDecision.ALLOW_ONE_MESSAGE,
    }:
        raise RuntimeError(f"dry-run gate denied preparation: {report.decision.value}")
    selected = provider or DryRunProvider()
    return selected.send(draft)
