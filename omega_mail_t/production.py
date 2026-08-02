"""One-message production connector with explicit, layered operator locks."""
from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
import os
import smtplib
import ssl
from typing import Protocol

from .officialization import OfficialDecision, OfficialGateReport, OfficialMessageDraft


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    provider: str
    status: str
    message_hash: str
    recipient: str
    provider_message_id: str | None = None
    detail: str = ""

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "status": self.status,
            "message_hash": self.message_hash,
            "recipient": self.recipient,
            "provider_message_id": self.provider_message_id,
            "detail": self.detail,
        }


class MailProvider(Protocol):
    name: str

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
        ...


class DryRunProvider:
    name = "dry-run"

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
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


class SMTPProvider:
    """SMTP provider limited to one pre-approved recipient per invocation."""

    name = "smtp"

    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    def send(self, draft: OfficialMessageDraft) -> DeliveryReceipt:
        if os.getenv("OMEGA_MAIL_EXTERNAL_SEND") != "I_ACKNOWLEDGE_ONE_MESSAGE":
            raise RuntimeError("external-send acknowledgement is absent")
        if len(draft.recipients) != 1:
            raise RuntimeError("SMTPProvider permits exactly one recipient")
        recipient = draft.recipients[0]
        allowlisted = (os.getenv("OMEGA_MAIL_ALLOWED_RECIPIENT") or "").strip().casefold()
        if not allowlisted or recipient != allowlisted:
            raise RuntimeError("recipient does not match OMEGA_MAIL_ALLOWED_RECIPIENT")

        message = EmailMessage()
        message["From"] = draft.sender
        message["To"] = recipient
        message["Subject"] = draft.subject
        message["Message-ID"] = make_msgid(domain=draft.sender.rsplit("@", 1)[1])
        message.set_content(draft.body)

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
                if self.config.starttls:
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


def deliver_one(
    *,
    report: OfficialGateReport,
    draft: OfficialMessageDraft,
    execute: bool = False,
    provider: MailProvider | None = None,
) -> DeliveryReceipt:
    """Deliver one message, or produce a no-network dry-run receipt."""
    if execute:
        if report.decision != OfficialDecision.ALLOW_ONE_MESSAGE:
            raise RuntimeError(f"production gate denied send: {report.decision.value}")
        selected = provider or SMTPProvider(SMTPConfig.from_env())
    else:
        if report.decision not in {
            OfficialDecision.ALLOW_DRY_RUN,
            OfficialDecision.ALLOW_ONE_MESSAGE,
        }:
            raise RuntimeError(f"dry-run gate denied preparation: {report.decision.value}")
        selected = provider or DryRunProvider()
    return selected.send(draft)
