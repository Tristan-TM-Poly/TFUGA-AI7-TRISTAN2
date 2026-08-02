from datetime import datetime, timedelta, timezone

import pytest

from omega_mail_t.hardening import OneMessageLedger
from omega_mail_t.officialization import (
    ApprovalRecord,
    OfficialDecision,
    OfficialGateReport,
    OfficialMessageDraft,
)
from omega_mail_t.production import (
    DeliveryReceipt,
    SMTPConfig,
    deliver_one,
    render_message,
)


def draft(**changes) -> OfficialMessageDraft:
    data = dict(
        sender="corporate@tristan.example",
        recipients=("known.partner@example.net",),
        subject="Avis administratif",
        body="Message administratif vérifié.",
        attachments=(),
        metadata={"purpose": "r04-hardening-test"},
    )
    data.update(changes)
    return OfficialMessageDraft(**data)


def allowed_report(message: OfficialMessageDraft) -> OfficialGateReport:
    return OfficialGateReport(
        decision=OfficialDecision.ALLOW_ONE_MESSAGE,
        reasons=(),
        checks={"human_approval": True},
        message_hash=message.content_hash,
    )


class AcceptedProvider:
    name = "accepted-test-provider"

    def __init__(self) -> None:
        self.calls = 0

    def send(self, message: OfficialMessageDraft) -> DeliveryReceipt:
        self.calls += 1
        return DeliveryReceipt(
            provider=self.name,
            status="ACCEPTED_BY_PROVIDER",
            message_hash=message.content_hash,
            recipient=message.recipients[0],
            provider_message_id="<accepted@test.invalid>",
        )


def test_subject_header_injection_is_blocked():
    message = draft(subject="Valid\nBcc: hidden@example.net")
    with pytest.raises(RuntimeError, match="subject_header_injection_detected"):
        deliver_one(
            report=allowed_report(message),
            draft=message,
            execute=False,
        )


def test_attachments_are_blocked_until_content_addressed():
    message = draft(attachments=("unverified-contract.pdf",))
    with pytest.raises(RuntimeError, match="attachments_require_content_addressed_pipeline"):
        deliver_one(
            report=allowed_report(message),
            draft=message,
            execute=False,
        )


def test_rendered_message_id_is_bound_to_content_hash():
    message = draft()
    first = render_message(message)
    second = render_message(message)
    assert first["Message-ID"] == second["Message-ID"]
    assert message.content_hash.removeprefix("sha256:")[:32] in first["Message-ID"]
    assert first["Bcc"] is None


def test_stale_approval_is_blocked_before_provider_call(tmp_path):
    message = draft()
    approved_at = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    approval = ApprovalRecord.create(
        message,
        approver="Tristan",
        approved_at=approved_at,
    )
    provider = AcceptedProvider()
    with pytest.raises(RuntimeError, match="execution_approval_expired"):
        deliver_one(
            report=allowed_report(message),
            draft=message,
            execute=True,
            provider=provider,
            approval=approval,
            ledger=OneMessageLedger(tmp_path / "ledger.jsonl"),
            now=approved_at + timedelta(hours=2),
        )
    assert provider.calls == 0


def test_execution_ledger_blocks_replay(tmp_path):
    instant = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    message = draft()
    approval = ApprovalRecord.create(message, approver="Tristan", approved_at=instant)
    provider = AcceptedProvider()
    ledger = OneMessageLedger(tmp_path / "ledger.jsonl")

    receipt = deliver_one(
        report=allowed_report(message),
        draft=message,
        execute=True,
        provider=provider,
        approval=approval,
        ledger=ledger,
        now=instant + timedelta(minutes=5),
    )
    assert receipt.reservation_id
    assert receipt.ledger_entry_hash
    assert provider.calls == 1
    assert ledger.audit()["entries"] == 2

    with pytest.raises(RuntimeError, match="already reserved or consumed"):
        deliver_one(
            report=allowed_report(message),
            draft=message,
            execute=True,
            provider=provider,
            approval=approval,
            ledger=ledger,
            now=instant + timedelta(minutes=6),
        )
    assert provider.calls == 1


def test_execution_ledger_detects_tampering(tmp_path):
    instant = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    message = draft()
    approval = ApprovalRecord.create(message, approver="Tristan", approved_at=instant)
    path = tmp_path / "ledger.jsonl"
    deliver_one(
        report=allowed_report(message),
        draft=message,
        execute=True,
        provider=AcceptedProvider(),
        approval=approval,
        ledger=OneMessageLedger(path),
        now=instant + timedelta(minutes=1),
    )
    path.write_text(
        path.read_text(encoding="utf-8").replace("RESERVED", "ALTERED", 1),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="entry hash mismatch"):
        OneMessageLedger(path).audit()


def test_smtp_transport_requires_encryption_and_exact_endpoint(monkeypatch):
    monkeypatch.setenv("OMEGA_MAIL_ALLOWED_SMTP_HOST", "smtp.example.net")
    monkeypatch.setenv("OMEGA_MAIL_ALLOWED_SMTP_PORT", "465")
    insecure = SMTPConfig(
        host="smtp.example.net",
        port=465,
        username="user",
        password="secret",
        use_ssl=False,
        starttls=False,
    )
    with pytest.raises(RuntimeError, match="exactly one"):
        insecure.validate_transport()

    secure = SMTPConfig(
        host="smtp.example.net",
        port=465,
        username="user",
        password="secret",
        use_ssl=True,
        starttls=False,
    )
    secure.validate_transport()
