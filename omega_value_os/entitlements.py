"""Provider-neutral paid-account entitlement bridge.

Payment providers produce signed/verified events. This module consumes only a
normalized event and never creates charges, refunds, payouts, or subscriptions.
It keeps payment authority separate from application access authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Set, Tuple


class EntitlementEventType(str, Enum):
    GRANT = "grant"
    REVOKE = "revoke"


@dataclass(frozen=True)
class EntitlementEvent:
    event_id: str
    account_id: str
    capability: str
    event_type: EntitlementEventType
    provider: str
    verified: bool
    evidence_ref: str


@dataclass
class EntitlementLedger:
    """Idempotent entitlement state derived from verified provider events."""

    _capabilities: Dict[str, Set[str]] = field(default_factory=dict)
    _processed_events: Set[str] = field(default_factory=set)
    _audit: list[Tuple[str, str, str, str]] = field(default_factory=list)

    def apply(self, event: EntitlementEvent) -> bool:
        if not event.event_id or not event.evidence_ref:
            raise ValueError("event_id and evidence_ref are required")
        if not event.verified:
            raise PermissionError("unverified provider event cannot change entitlements")
        if event.event_id in self._processed_events:
            return False

        capabilities = self._capabilities.setdefault(event.account_id, set())
        if event.event_type is EntitlementEventType.GRANT:
            capabilities.add(event.capability)
        elif event.event_type is EntitlementEventType.REVOKE:
            capabilities.discard(event.capability)
        else:
            raise ValueError(f"unsupported event type: {event.event_type}")

        self._processed_events.add(event.event_id)
        self._audit.append(
            (event.event_id, event.account_id, event.capability, event.event_type.value)
        )
        return True

    def capabilities_for(self, account_id: str) -> FrozenSet[str]:
        return frozenset(self._capabilities.get(account_id, set()))

    def audit_log(self) -> Tuple[Tuple[str, str, str, str], ...]:
        return tuple(self._audit)
