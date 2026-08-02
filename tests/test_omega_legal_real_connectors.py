from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs

import pytest

from omega_legal_production_os_t.http_client import HttpResponse
from omega_legal_production_os_t.models import (
    ActionState,
    ActionType,
    ApprovalRecord,
    ExternalActionEnvelope,
    RiskLevel,
)
from omega_legal_production_os_t.real_execution import doctor, execute_action
from omega_legal_production_os_t.real_providers import (
    DropboxSignTestProvider,
    GmailSendProvider,
    GitHubDraftReleaseProvider,
    ProviderError,
    StripeTestPaymentProvider,
)


class FakeTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def request(self, method, url, *, headers=None, body=None, timeout=30.0):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers or {}),
                "body": body,
                "timeout": timeout,
            }
        )
        if not self.responses:
            raise AssertionError("unexpected network request")
        return self.responses.pop(0)


def response(status: int, payload: Mapping | None = None) -> HttpResponse:
    return HttpResponse(
        status=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload or {}).encode(),
    )


def text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.strip().casefold().encode()).hexdigest()


def bytes_hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def approved_action(
    action_type: ActionType,
    payload: dict,
    *,
    action_id: str,
    approvals: int = 1,
) -> ExternalActionEnvelope:
    action = ExternalActionEnvelope(
        action_id=action_id,
        action_type=action_type,
        company_id="tristan_parent_opco",
        requested_by="tristan",
        requested_at="2026-08-02T22:00:00Z",
        purpose="Real connector test",
        payload=payload,
        required_approvals=approvals,
        risk_level=RiskLevel.MEDIUM,
        state=ActionState.APPROVED,
    )
    records = [
        ApprovalRecord.create(action, approver=f"approver-{index}", role="director")
        for index in range(1, approvals + 1)
    ]
    return replace(action, approvals=tuple(records))


def env_for(action: ExternalActionEnvelope, provider: str, **extra: str) -> dict[str, str]:
    result = {
        "OMEGA_EXTERNAL_EXECUTION_ACK": "I_ACKNOWLEDGE_ONE_ACTION",
        "OMEGA_ALLOWED_ACTION_ID": action.action_id,
        "OMEGA_ALLOWED_ACTION_HASH": action.action_hash,
        "OMEGA_ALLOWED_PROVIDER": provider,
    }
    result.update(extra)
    return result


def write_action(path: Path, action: ExternalActionEnvelope) -> None:
    path.write_text(json.dumps(action.to_mapping()), encoding="utf-8")


def test_missing_interlock_does_not_consume_reservation(tmp_path: Path) -> None:
    action = approved_action(
        ActionType.PAYMENT,
        {"amount_cents": 500, "currency": "cad", "confirm": False},
        action_id="ACT-NO-ACK",
    )
    action_path = tmp_path / "action.json"
    write_action(action_path, action)
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(ProviderError, match="acknowledgement"):
        execute_action(
            action_path,
            provider_name="stripe-test-payment-intent",
            ledger_path=ledger,
            receipt_path=tmp_path / "receipt.json",
            env={},
            transport=FakeTransport([]),
        )
    assert not ledger.exists()


def test_gmail_builds_real_rfc_message_and_dedupes_by_message_id() -> None:
    recipient = "external@example.com"
    action = approved_action(
        ActionType.EXTERNAL_MAIL,
        {
            "recipient_hash": text_hash(recipient),
            "subject": "Omega real mail",
            "body_text": "This is one exact approved message.",
        },
        action_id="ACT-GMAIL-001",
    )
    transport = FakeTransport(
        [
            response(200, {"resultSizeEstimate": 0}),
            response(200, {"id": "gmail-message-1", "threadId": "thread-1"}),
        ]
    )
    receipt = GmailSendProvider(transport).execute(
        action,
        env=env_for(
            action,
            "gmail-send",
            GMAIL_ACCESS_TOKEN="oauth-token",
            OMEGA_RECIPIENT_EMAIL=recipient,
            OMEGA_SENDER_EMAIL="sender@example.com",
            OMEGA_MESSAGE_ID_DOMAIN="example.com",
        ),
    )
    assert receipt.external_id == "gmail-message-1"
    assert len(transport.calls) == 2
    assert "rfc822msgid" in transport.calls[0]["url"]
    sent = json.loads(transport.calls[1]["body"])
    decoded = base64.urlsafe_b64decode(sent["raw"]).decode("utf-8")
    assert "To: external@example.com" in decoded
    assert "Subject: Omega real mail" in decoded
    assert "Message-ID:" in decoded
    assert transport.calls[1]["headers"]["Authorization"] == "Bearer oauth-token"


def test_gmail_existing_message_prevents_second_send() -> None:
    recipient = "existing@example.com"
    action = approved_action(
        ActionType.EXTERNAL_MAIL,
        {"recipient_hash": text_hash(recipient), "subject": "Existing", "body_text": "Body"},
        action_id="ACT-GMAIL-002",
    )
    transport = FakeTransport([response(200, {"messages": [{"id": "m-existing", "threadId": "t"}]})])
    receipt = GmailSendProvider(transport).execute(
        action,
        env=env_for(
            action,
            "gmail-send",
            GMAIL_ACCESS_TOKEN="oauth-token",
            OMEGA_RECIPIENT_EMAIL=recipient,
        ),
    )
    assert receipt.status == "DEDUPLICATED_EXISTING_MESSAGE"
    assert len(transport.calls) == 1


def test_github_provider_creates_draft_only() -> None:
    action = approved_action(
        ActionType.RELEASE,
        {
            "repository": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
            "tag_name": "v3.4.0-rc1",
            "target_commitish": "abc1234",
            "name": "R0.3 candidate",
            "body": "Draft candidate",
            "draft": True,
            "prerelease": True,
        },
        action_id="ACT-REL-001",
    )
    transport = FakeTransport(
        [
            response(404, {"message": "Not Found"}),
            response(201, {"id": 77, "tag_name": "v3.4.0-rc1", "draft": True, "html_url": "https://example"}),
        ]
    )
    receipt = GitHubDraftReleaseProvider(transport).execute(
        action,
        env=env_for(action, "github-release-draft", GITHUB_RELEASE_TOKEN="token"),
    )
    assert receipt.status == "DRAFT_RELEASE_CREATED"
    payload = json.loads(transport.calls[1]["body"])
    assert payload["draft"] is True
    assert transport.calls[1]["headers"]["X-GitHub-Api-Version"] == "2026-03-10"


def test_github_provider_refuses_public_release() -> None:
    action = approved_action(
        ActionType.RELEASE,
        {"repository": "owner/repo", "tag_name": "v1.0.0", "draft": False},
        action_id="ACT-REL-002",
    )
    with pytest.raises(ProviderError, match="draft"):
        GitHubDraftReleaseProvider(FakeTransport([])).execute(
            action,
            env=env_for(action, "github-release-draft", GITHUB_RELEASE_TOKEN="token"),
        )


def test_stripe_creates_test_payment_intent_with_idempotency() -> None:
    action = approved_action(
        ActionType.PAYMENT,
        {"amount_cents": 2500, "currency": "cad", "description": "Test invoice", "confirm": False},
        action_id="ACT-PAY-001",
        approvals=2,
    )
    transport = FakeTransport(
        [response(200, {"id": "pi_test_1", "status": "requires_payment_method", "livemode": False, "amount": 2500, "currency": "cad"})]
    )
    receipt = StripeTestPaymentProvider(transport).execute(
        action,
        env=env_for(action, "stripe-test-payment-intent", STRIPE_SECRET_KEY="sk_test_example"),
    )
    assert receipt.external_id == "pi_test_1"
    assert transport.calls[0]["headers"]["Idempotency-Key"] == action.action_hash
    fields = parse_qs(transport.calls[0]["body"].decode())
    assert fields["amount"] == ["2500"]
    assert fields["currency"] == ["cad"]
    assert "confirm" not in fields


def test_stripe_live_key_is_impossible() -> None:
    action = approved_action(
        ActionType.PAYMENT,
        {"amount_cents": 500, "currency": "cad", "confirm": False},
        action_id="ACT-PAY-002",
    )
    with pytest.raises(ProviderError, match="test-mode"):
        StripeTestPaymentProvider(FakeTransport([])).execute(
            action,
            env=env_for(action, "stripe-test-payment-intent", STRIPE_SECRET_KEY="sk_live_forbidden"),
        )


def test_dropbox_sign_sends_only_non_binding_test_request(tmp_path: Path) -> None:
    document = b"%PDF-1.4\nOmega test document\n"
    document_path = tmp_path / "contract.pdf"
    document_path.write_bytes(document)
    signer = "signer@example.com"
    action = approved_action(
        ActionType.SIGNATURE,
        {
            "document_path": str(document_path),
            "document_hash": bytes_hash(document),
            "signer_email_hash": text_hash(signer),
            "signer_name": "Test Signer",
            "title": "Non-binding test",
            "subject": "Test signature request",
            "message": "This request is not legally binding.",
        },
        action_id="ACT-SIGN-001",
        approvals=2,
    )
    transport = FakeTransport(
        [response(200, {"signature_request": {"signature_request_id": "sig-test-1", "test_mode": True, "is_complete": False}})]
    )
    receipt = DropboxSignTestProvider(transport).execute(
        action,
        env=env_for(
            action,
            "dropbox-sign-test",
            DROPBOX_SIGN_API_KEY="api-key",
            OMEGA_SIGNER_EMAIL=signer,
        ),
    )
    assert receipt.status == "TEST_SIGNATURE_REQUEST_SENT"
    body = transport.calls[0]["body"]
    assert b'name="test_mode"\r\n\r\n1' in body
    assert signer.encode() in body
    assert document in body


def test_end_to_end_execution_writes_ledger_and_blocks_replay(tmp_path: Path) -> None:
    action = approved_action(
        ActionType.PAYMENT,
        {"amount_cents": 100, "currency": "cad", "confirm": False},
        action_id="ACT-PAY-REPLAY",
    )
    action_path = tmp_path / "action.json"
    write_action(action_path, action)
    env = env_for(action, "stripe-test-payment-intent", STRIPE_SECRET_KEY="sk_test_example")
    ledger_path = tmp_path / "ledger.jsonl"
    first = FakeTransport(
        [response(200, {"id": "pi_once", "status": "requires_payment_method", "livemode": False, "amount": 100, "currency": "cad"})]
    )
    receipt = execute_action(
        action_path,
        provider_name="stripe-test-payment-intent",
        ledger_path=ledger_path,
        receipt_path=tmp_path / "receipt.json",
        env=env,
        transport=first,
    )
    assert receipt.provider_receipt.external_id == "pi_once"
    events = [json.loads(line)["event"] for line in ledger_path.read_text().splitlines()]
    assert events == ["RESERVED", "EXECUTION_STARTED", "PROVIDER_ACCEPTED", "EFFECT_CONFIRMED"]
    with pytest.raises(RuntimeError, match="replay"):
        execute_action(
            action_path,
            provider_name="stripe-test-payment-intent",
            ledger_path=ledger_path,
            receipt_path=tmp_path / "receipt-2.json",
            env=env,
            transport=FakeTransport([]),
        )


def test_doctor_never_prints_secret_values() -> None:
    result = doctor(
        "stripe-test-payment-intent",
        env={
            "OMEGA_EXTERNAL_EXECUTION_ACK": "I_ACKNOWLEDGE_ONE_ACTION",
            "OMEGA_ALLOWED_ACTION_ID": "ACT-1",
            "OMEGA_ALLOWED_ACTION_HASH": "sha256:" + "a" * 64,
            "OMEGA_ALLOWED_PROVIDER": "stripe-test-payment-intent",
            "STRIPE_SECRET_KEY": "sk_test_super_secret",
        },
    )
    assert result["ready"] is True
    assert result["secrets_printed"] is False
    assert "sk_test_super_secret" not in json.dumps(result)
