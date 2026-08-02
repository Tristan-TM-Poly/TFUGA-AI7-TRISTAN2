"""Real provider adapters for bounded external execution.

These adapters perform actual HTTPS calls when supplied with credentials. Gmail
can send one exact message, GitHub can create one draft release, Stripe can
create one test-mode PaymentIntent, and Dropbox Sign can create one non-binding
test signature request. No adapter accepts live payment or binding signature
credentials in this release.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from email.message import EmailMessage
import hashlib
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Mapping, MutableMapping
from urllib.parse import quote

from .http_client import HttpResponse, HttpTransport, UrllibTransport, form_body, json_body, multipart_body
from .models import ActionState, ActionType, ExternalActionEnvelope


EXECUTION_ACK = "I_ACKNOWLEDGE_ONE_ACTION"


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderReceipt:
    provider: str
    operation: str
    external_id: str
    status: str
    effect_confirmed: bool
    details: Mapping[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "external_id": self.external_id,
            "status": self.status,
            "effect_confirmed": self.effect_confirmed,
            "details": dict(self.details),
        }


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.strip().casefold().encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _required_env(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ProviderError(f"missing required environment variable: {name}")
    return value


def assert_execution_interlock(
    action: ExternalActionEnvelope,
    provider: str,
    *,
    env: Mapping[str, str] | None = None,
) -> None:
    values = env or os.environ
    if values.get("OMEGA_EXTERNAL_EXECUTION_ACK") != EXECUTION_ACK:
        raise ProviderError("external execution acknowledgement missing")
    if values.get("OMEGA_ALLOWED_ACTION_ID") != action.action_id:
        raise ProviderError("exact action id is not allowlisted")
    if values.get("OMEGA_ALLOWED_ACTION_HASH") != action.action_hash:
        raise ProviderError("exact action hash is not allowlisted")
    if values.get("OMEGA_ALLOWED_PROVIDER") != provider:
        raise ProviderError("exact provider is not allowlisted")
    if action.state is not ActionState.APPROVED:
        raise ProviderError("action must be in APPROVED state")
    valid_approvers = {
        approval.approver.strip().casefold()
        for approval in action.approvals
        if not approval.validate_for(action)
    }
    if len(valid_approvers) < action.required_approvals:
        raise ProviderError("required distinct approvals are missing")


def _json_or_error(response: HttpResponse, provider: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise ProviderError(f"{provider} returned invalid JSON with HTTP {response.status}") from exc
    if not 200 <= response.status < 300:
        compact = json.dumps(payload, sort_keys=True)[:500]
        raise ProviderError(f"{provider} rejected request with HTTP {response.status}: {compact}")
    return payload


class GmailSendProvider:
    name = "gmail-send"
    send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    messages_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    def __init__(self, transport: HttpTransport | None = None) -> None:
        self.transport = transport or UrllibTransport()

    def execute(
        self,
        action: ExternalActionEnvelope,
        *,
        env: Mapping[str, str] | None = None,
    ) -> ProviderReceipt:
        values = env or os.environ
        assert_execution_interlock(action, self.name, env=values)
        if action.action_type is not ActionType.EXTERNAL_MAIL:
            raise ProviderError("gmail provider requires EXTERNAL_MAIL action")
        token = _required_env(values, "GMAIL_ACCESS_TOKEN")
        recipient = _required_env(values, "OMEGA_RECIPIENT_EMAIL")
        expected_hash = str(action.payload.get("recipient_hash", ""))
        if expected_hash != _sha256_text(recipient):
            raise ProviderError("recipient email does not match content-addressed recipient hash")
        subject = str(action.payload.get("subject", "")).strip()
        body_text = str(action.payload.get("body_text", ""))
        if not subject or not body_text:
            raise ProviderError("subject and body_text are required")
        sender = values.get("OMEGA_SENDER_EMAIL", "").strip()
        domain = values.get("OMEGA_MESSAGE_ID_DOMAIN", "omega.invalid").strip().lower()
        message_id = f"<{action.action_hash.removeprefix('sha256:')}@{domain}>"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        query_url = f"{self.messages_url}?q={quote('rfc822msgid:' + message_id)}&maxResults=1"
        existing = self.transport.request("GET", query_url, headers=headers)
        if existing.status == 200:
            data = existing.json()
            messages = data.get("messages", [])
            if messages:
                external_id = str(messages[0]["id"])
                return ProviderReceipt(
                    provider=self.name,
                    operation="messages.send",
                    external_id=external_id,
                    status="DEDUPLICATED_EXISTING_MESSAGE",
                    effect_confirmed=True,
                    details={"message_id": message_id, "thread_id": messages[0].get("threadId")},
                )

        message = EmailMessage()
        message["To"] = recipient
        if sender:
            message["From"] = sender
        message["Subject"] = subject
        message["Message-ID"] = message_id
        if action.payload.get("in_reply_to"):
            message["In-Reply-To"] = str(action.payload["in_reply_to"])
        if action.payload.get("references"):
            message["References"] = str(action.payload["references"])
        message.set_content(body_text)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        request_payload: MutableMapping[str, Any] = {"raw": raw}
        if action.payload.get("thread_id"):
            request_payload["threadId"] = str(action.payload["thread_id"])
        response = self.transport.request(
            "POST",
            self.send_url,
            headers={**headers, "Content-Type": "application/json"},
            body=json_body(request_payload),
        )
        data = _json_or_error(response, self.name)
        return ProviderReceipt(
            provider=self.name,
            operation="messages.send",
            external_id=str(data["id"]),
            status="PROVIDER_ACCEPTED",
            effect_confirmed=False,
            details={"thread_id": data.get("threadId"), "message_id": message_id},
        )

    def reconcile(self, receipt: ProviderReceipt, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        token = _required_env(values, "GMAIL_ACCESS_TOKEN")
        response = self.transport.request(
            "GET",
            f"{self.messages_url}/{quote(receipt.external_id)}?format=metadata",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        data = _json_or_error(response, self.name)
        return ProviderReceipt(
            provider=self.name,
            operation="messages.get",
            external_id=str(data["id"]),
            status="MESSAGE_PRESENT_IN_SENT_MAILBOX",
            effect_confirmed=True,
            details={"thread_id": data.get("threadId"), "label_ids": data.get("labelIds", [])},
        )


class GitHubDraftReleaseProvider:
    name = "github-release-draft"
    api_base = "https://api.github.com"

    def __init__(self, transport: HttpTransport | None = None) -> None:
        self.transport = transport or UrllibTransport()

    def execute(self, action: ExternalActionEnvelope, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        assert_execution_interlock(action, self.name, env=values)
        if action.action_type is not ActionType.RELEASE:
            raise ProviderError("GitHub release provider requires RELEASE action")
        token = _required_env(values, "GITHUB_RELEASE_TOKEN")
        repository = str(action.payload.get("repository", ""))
        if repository.count("/") != 1:
            raise ProviderError("repository must be owner/name")
        tag_name = str(action.payload.get("tag_name", "")).strip()
        if not tag_name:
            raise ProviderError("tag_name is required")
        if action.payload.get("draft") is not True:
            raise ProviderError("R0.3 only permits draft GitHub releases")
        common_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        }
        by_tag = f"{self.api_base}/repos/{repository}/releases/tags/{quote(tag_name, safe='')}"
        existing = self.transport.request("GET", by_tag, headers=common_headers)
        if existing.status == 200:
            data = existing.json()
            return ProviderReceipt(
                provider=self.name,
                operation="releases.get_by_tag",
                external_id=str(data["id"]),
                status="DEDUPLICATED_EXISTING_RELEASE",
                effect_confirmed=bool(data.get("draft")),
                details={"tag_name": data.get("tag_name"), "draft": data.get("draft")},
            )
        payload = {
            "tag_name": tag_name,
            "target_commitish": str(action.payload.get("target_commitish", "main")),
            "name": str(action.payload.get("name", tag_name)),
            "body": str(action.payload.get("body", "")),
            "draft": True,
            "prerelease": bool(action.payload.get("prerelease", False)),
            "generate_release_notes": bool(action.payload.get("generate_release_notes", False)),
        }
        response = self.transport.request(
            "POST",
            f"{self.api_base}/repos/{repository}/releases",
            headers={**common_headers, "Content-Type": "application/json"},
            body=json_body(payload),
        )
        data = _json_or_error(response, self.name)
        if data.get("draft") is not True:
            raise ProviderError("GitHub response was not a draft release")
        return ProviderReceipt(
            provider=self.name,
            operation="releases.create",
            external_id=str(data["id"]),
            status="DRAFT_RELEASE_CREATED",
            effect_confirmed=True,
            details={"tag_name": data.get("tag_name"), "draft": True, "html_url": data.get("html_url")},
        )

    def reconcile(self, receipt: ProviderReceipt, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        token = _required_env(values, "GITHUB_RELEASE_TOKEN")
        repository = _required_env(values, "OMEGA_RELEASE_REPOSITORY")
        response = self.transport.request(
            "GET",
            f"{self.api_base}/repos/{repository}/releases/{quote(receipt.external_id)}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )
        data = _json_or_error(response, self.name)
        return ProviderReceipt(
            provider=self.name,
            operation="releases.get",
            external_id=str(data["id"]),
            status="DRAFT_RELEASE_PRESENT" if data.get("draft") else "RELEASE_STATE_CHANGED",
            effect_confirmed=bool(data.get("draft")),
            details={"tag_name": data.get("tag_name"), "draft": data.get("draft")},
        )


class StripeTestPaymentProvider:
    name = "stripe-test-payment-intent"
    api_base = "https://api.stripe.com/v1"

    def __init__(self, transport: HttpTransport | None = None) -> None:
        self.transport = transport or UrllibTransport()

    def _headers(self, key: str, action_hash: str | None = None) -> dict[str, str]:
        basic = base64.b64encode(f"{key}:".encode()).decode()
        headers = {"Authorization": f"Basic {basic}", "Accept": "application/json"}
        if action_hash:
            headers["Idempotency-Key"] = action_hash
        return headers

    def execute(self, action: ExternalActionEnvelope, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        assert_execution_interlock(action, self.name, env=values)
        if action.action_type is not ActionType.PAYMENT:
            raise ProviderError("Stripe provider requires PAYMENT action")
        key = _required_env(values, "STRIPE_SECRET_KEY")
        if not key.startswith("sk_test_"):
            raise ProviderError("only Stripe test-mode secret keys are accepted")
        if bool(action.payload.get("confirm", False)):
            raise ProviderError("automatic confirmation is forbidden in R0.4")
        amount = int(action.payload.get("amount_cents", 0))
        currency = str(action.payload.get("currency", "cad")).lower()
        if amount <= 0 or currency != "cad":
            raise ProviderError("positive CAD amount_cents is required")
        fields: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "description": str(action.payload.get("description", action.purpose)),
            "automatic_payment_methods[enabled]": "true",
            "metadata[action_id]": action.action_id,
            "metadata[action_hash]": action.action_hash,
            "metadata[company_id]": action.company_id,
        }
        response = self.transport.request(
            "POST",
            f"{self.api_base}/payment_intents",
            headers={**self._headers(key, action.action_hash), "Content-Type": "application/x-www-form-urlencoded"},
            body=form_body(fields),
        )
        data = _json_or_error(response, self.name)
        if data.get("livemode") is not False:
            raise ProviderError("Stripe response is not test mode")
        return ProviderReceipt(
            provider=self.name,
            operation="payment_intents.create",
            external_id=str(data["id"]),
            status=str(data.get("status", "created")),
            effect_confirmed=True,
            details={"livemode": False, "amount": data.get("amount"), "currency": data.get("currency")},
        )

    def reconcile(self, receipt: ProviderReceipt, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        key = _required_env(values, "STRIPE_SECRET_KEY")
        if not key.startswith("sk_test_"):
            raise ProviderError("only Stripe test-mode secret keys are accepted")
        response = self.transport.request(
            "GET",
            f"{self.api_base}/payment_intents/{quote(receipt.external_id)}",
            headers=self._headers(key),
        )
        data = _json_or_error(response, self.name)
        if data.get("livemode") is not False:
            raise ProviderError("Stripe reconciliation returned live-mode object")
        return ProviderReceipt(
            provider=self.name,
            operation="payment_intents.retrieve",
            external_id=str(data["id"]),
            status=str(data.get("status", "unknown")),
            effect_confirmed=True,
            details={"livemode": False, "amount": data.get("amount"), "currency": data.get("currency")},
        )


class DropboxSignTestProvider:
    name = "dropbox-sign-test"
    api_base = "https://api.hellosign.com/v3"

    def __init__(self, transport: HttpTransport | None = None) -> None:
        self.transport = transport or UrllibTransport()

    @staticmethod
    def _headers(key: str) -> dict[str, str]:
        basic = base64.b64encode(f"{key}:".encode()).decode()
        return {"Authorization": f"Basic {basic}", "Accept": "application/json"}

    def execute(self, action: ExternalActionEnvelope, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        assert_execution_interlock(action, self.name, env=values)
        if action.action_type is not ActionType.SIGNATURE:
            raise ProviderError("Dropbox Sign provider requires SIGNATURE action")
        key = _required_env(values, "DROPBOX_SIGN_API_KEY")
        signer_email = _required_env(values, "OMEGA_SIGNER_EMAIL")
        if str(action.payload.get("signer_email_hash", "")) != _sha256_text(signer_email):
            raise ProviderError("signer email does not match content-addressed signer hash")
        document_path = Path(str(action.payload.get("document_path", "")))
        if not document_path.is_file():
            raise ProviderError("document_path does not exist")
        document = document_path.read_bytes()
        if str(action.payload.get("document_hash", "")) != _sha256_bytes(document):
            raise ProviderError("document hash mismatch")
        signer_name = str(action.payload.get("signer_name", "")).strip()
        if not signer_name:
            raise ProviderError("signer_name is required")
        fields = [
            ("title", str(action.payload.get("title", document_path.name))),
            ("subject", str(action.payload.get("subject", "Signature test request"))),
            ("message", str(action.payload.get("message", "Non-binding test signature request."))),
            ("signers[0][email_address]", signer_email),
            ("signers[0][name]", signer_name),
            ("signers[0][order]", "0"),
            ("metadata[action_id]", action.action_id),
            ("metadata[action_hash]", action.action_hash),
            ("test_mode", "1"),
        ]
        content_type = mimetypes.guess_type(document_path.name)[0] or "application/pdf"
        body, multipart_type = multipart_body(
            fields=fields,
            files=[("files[0]", document_path.name, content_type, document)],
        )
        response = self.transport.request(
            "POST",
            f"{self.api_base}/signature_request/send",
            headers={**self._headers(key), "Content-Type": multipart_type},
            body=body,
        )
        data = _json_or_error(response, self.name)
        request_data = data.get("signature_request")
        if not isinstance(request_data, Mapping) or request_data.get("test_mode") is not True:
            raise ProviderError("Dropbox Sign response is not non-binding test mode")
        return ProviderReceipt(
            provider=self.name,
            operation="signature_request.send",
            external_id=str(request_data["signature_request_id"]),
            status="TEST_SIGNATURE_REQUEST_SENT",
            effect_confirmed=False,
            details={"test_mode": True, "is_complete": request_data.get("is_complete", False)},
        )

    def reconcile(self, receipt: ProviderReceipt, *, env: Mapping[str, str] | None = None) -> ProviderReceipt:
        values = env or os.environ
        key = _required_env(values, "DROPBOX_SIGN_API_KEY")
        response = self.transport.request(
            "GET",
            f"{self.api_base}/signature_request/{quote(receipt.external_id)}",
            headers=self._headers(key),
        )
        data = _json_or_error(response, self.name)
        request_data = data.get("signature_request")
        if not isinstance(request_data, Mapping) or request_data.get("test_mode") is not True:
            raise ProviderError("Dropbox Sign reconciliation is not test mode")
        return ProviderReceipt(
            provider=self.name,
            operation="signature_request.get",
            external_id=str(request_data["signature_request_id"]),
            status=(
                "TEST_SIGNATURE_COMPLETE"
                if request_data.get("is_complete")
                else "TEST_SIGNATURE_PENDING"
            ),
            effect_confirmed=bool(request_data.get("is_complete")),
            details={
                "test_mode": True,
                "is_complete": request_data.get("is_complete", False),
                "is_declined": request_data.get("is_declined", False),
                "has_error": request_data.get("has_error", False),
            },
        )


PROVIDERS = {
    GmailSendProvider.name: GmailSendProvider,
    GitHubDraftReleaseProvider.name: GitHubDraftReleaseProvider,
    StripeTestPaymentProvider.name: StripeTestPaymentProvider,
    DropboxSignTestProvider.name: DropboxSignTestProvider,
}
