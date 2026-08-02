"""Normalize inbound provider events into the common intake schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Channel, IntakeEvent, IntakeStatus
from .security import idempotency_key, is_auto_generated, normalize_address, scan_untrusted_text, sha256_value


@dataclass(slots=True)
class IntakeRegistry:
    seen_keys: set[str] = field(default_factory=set)

    def ingest_email(
        self,
        payload: dict[str, Any],
        *,
        owned_addresses: set[str] | None = None,
    ) -> IntakeEvent:
        required = ("event_id", "provider", "account", "external_id", "sender", "subject", "body", "recipients")
        missing = [name for name in required if name not in payload]
        if missing:
            raise ValueError("missing intake fields: " + ",".join(missing))

        sender = normalize_address(str(payload["sender"]))
        recipients = [normalize_address(str(item)) for item in payload["recipients"]]
        raw_hash = sha256_value(
            {
                "sender": sender,
                "recipients": recipients,
                "subject": payload["subject"],
                "body": payload["body"],
                "attachments": payload.get("attachments", []),
            }
        )
        key = idempotency_key(str(payload["provider"]), str(payload["external_id"]), raw_hash)
        if key in self.seen_keys:
            raise ValueError("duplicate intake event")
        self.seen_keys.add(key)

        headers = {str(k): str(v) for k, v in payload.get("headers", {}).items()}
        findings = scan_untrusted_text(str(payload["body"]))
        auto_generated = is_auto_generated(headers, sender, owned_addresses or set())
        status = IntakeStatus.QUARANTINED if findings else IntakeStatus.RECEIVED

        return IntakeEvent(
            event_id=str(payload["event_id"]),
            channel=Channel.EMAIL,
            provider=str(payload["provider"]),
            account=normalize_address(str(payload["account"])),
            external_id=str(payload["external_id"]),
            sender_address=sender,
            sender_name=str(payload.get("sender_name", "")),
            subject=str(payload["subject"]),
            body=str(payload["body"]),
            recipients=recipients,
            attachments=list(payload.get("attachments", [])),
            language=str(payload.get("language", "fr-CA")),
            status=status,
            raw_hash=raw_hash,
            metadata={
                "idempotency_key": key,
                "security_findings": list(findings),
                "auto_generated": auto_generated,
                "headers": headers,
            },
        )
