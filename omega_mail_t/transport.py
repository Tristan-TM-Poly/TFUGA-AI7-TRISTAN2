"""Deterministic in-memory mail transport for Ω-MAIL-T."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import MailMessage, Mailbox, normalize_address
from .oak import GateResult, OAKDecision, OAKMailGate


class DeliveryBlocked(RuntimeError):
    """Raised when OAK blocks a delivery."""


@dataclass(frozen=True, slots=True)
class TransportEvent:
    sequence: int
    event: str
    message_id: str
    mailbox: str | None
    details: dict[str, Any]


class InMemoryTransport:
    def __init__(self, gate: OAKMailGate | None = None) -> None:
        self.gate = gate or OAKMailGate()
        self.mailboxes: dict[str, Mailbox] = {}
        self.events: list[TransportEvent] = []

    def register(self, mailbox: Mailbox) -> None:
        address = normalize_address(mailbox.address)
        if address in self.mailboxes:
            raise ValueError(f"Mailbox already registered: {address}")
        self.mailboxes[address] = mailbox
        self._record("MAILBOX_REGISTERED", "registry", address, {"company_id": mailbox.company_id})

    def send(self, message: MailMessage) -> GateResult:
        result = self.gate.evaluate(message, set(self.mailboxes))
        self._record(
            "GATE_DECISION",
            message.message_id,
            None,
            {"decision": result.decision.value, "reasons": list(result.reasons)},
        )
        if result.decision != OAKDecision.ALLOW_SANDBOX:
            self._record("DELIVERY_BLOCKED", message.message_id, None, {"reasons": list(result.reasons)})
            raise DeliveryBlocked("; ".join(result.reasons))

        copies = max(1, int(message.metadata.get("duplicate_copies", 1)))
        for recipient in message.recipients:
            mailbox = self.mailboxes[recipient]
            for copy_index in range(copies):
                mailbox.receive(message)
                self._record(
                    "DELIVERED",
                    message.message_id,
                    recipient,
                    {"copy_index": copy_index, "thread_id": message.thread_id},
                )
        return result

    def _record(self, event: str, message_id: str, mailbox: str | None, details: dict[str, Any]) -> None:
        self.events.append(
            TransportEvent(
                sequence=len(self.events) + 1,
                event=event,
                message_id=message_id,
                mailbox=mailbox,
                details=details,
            )
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "mailboxes": {
                address: {
                    "company_id": mailbox.company_id,
                    "role": mailbox.role,
                    "message_count": len(mailbox.messages),
                    "message_ids": [message.message_id for message in mailbox.messages],
                }
                for address, mailbox in sorted(self.mailboxes.items())
            },
            "events": [asdict(event) for event in self.events],
        }
