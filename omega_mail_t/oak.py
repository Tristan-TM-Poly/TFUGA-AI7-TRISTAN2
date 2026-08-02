"""OAK safety gate for synthetic email transport."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import MailMessage, normalize_address


class OAKDecision(str, Enum):
    ALLOW_SANDBOX = "ALLOW_SANDBOX"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class GateResult:
    decision: OAKDecision
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.decision == OAKDecision.ALLOW_SANDBOX


class OAKMailGate:
    """Block every non-synthetic route by default.

    R0.1 permits only registered mailboxes under reserved ``.test`` domains and
    messages explicitly marked as synthetic. No external-network transport is
    implemented by this package.
    """

    def __init__(self, *, allowed_data_classifications: tuple[str, ...] = ("synthetic_internal",)) -> None:
        self.allowed_data_classifications = frozenset(allowed_data_classifications)

    def evaluate(self, message: MailMessage, registered_mailboxes: set[str]) -> GateResult:
        reasons: list[str] = []
        participants = (message.sender, *message.recipients)

        for raw in participants:
            address = normalize_address(raw)
            domain = address.rsplit("@", 1)[1]
            if not domain.endswith(".test"):
                reasons.append(f"non_test_domain:{domain}")

        unknown = sorted(set(message.recipients) - registered_mailboxes)
        if unknown:
            reasons.append("unregistered_recipient:" + ",".join(unknown))

        if message.sender not in registered_mailboxes:
            reasons.append(f"unregistered_sender:{message.sender}")

        if message.data_classification not in self.allowed_data_classifications:
            reasons.append(f"disallowed_data_classification:{message.data_classification}")

        if any(not attachment.synthetic for attachment in message.attachments):
            reasons.append("non_synthetic_attachment")

        if message.metadata.get("external_delivery") is True:
            reasons.append("external_delivery_requested")

        if reasons:
            return GateResult(OAKDecision.BLOCK, tuple(reasons))
        return GateResult(OAKDecision.ALLOW_SANDBOX, ("sandbox_only",))
