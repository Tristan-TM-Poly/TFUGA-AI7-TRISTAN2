from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .ledger import reject_sensitive_fields
from .privacy import reject_secret_values
from .transparency import digest_payload


@dataclass(frozen=True)
class ProviderEvent:
    source: str
    event_id: str
    gross_minor: int
    fee_minor: int
    currency: str
    occurred_at: str
    status: str = "paid"

    def validate(self) -> None:
        reject_sensitive_fields(asdict(self))
        reject_secret_values(asdict(self))
        if not self.source.strip() or not self.event_id.strip():
            raise ValueError("source and event_id are required")
        if self.gross_minor < 0 or self.fee_minor < 0 or self.fee_minor > self.gross_minor:
            raise ValueError("invalid provider money values")
        if len(self.currency) != 3:
            raise ValueError("currency must be a three-letter code")

    @property
    def net_minor(self) -> int:
        return self.gross_minor - self.fee_minor

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self) | {"net_minor": self.net_minor}


def reconcile_events(
    internal: Iterable[ProviderEvent],
    provider: Iterable[ProviderEvent],
) -> dict[str, Any]:
    def index(
        events: Iterable[ProviderEvent],
    ) -> tuple[dict[tuple[str, str], ProviderEvent], list[str]]:
        mapping: dict[tuple[str, str], ProviderEvent] = {}
        duplicates: list[str] = []
        for event in events:
            event.validate()
            key = (event.source, event.event_id)
            if key in mapping:
                duplicates.append(f"{event.source}:{event.event_id}")
            else:
                mapping[key] = event
        return mapping, sorted(duplicates)

    left, internal_duplicates = index(internal)
    right, provider_duplicates = index(provider)
    missing_internal = sorted(f"{s}:{e}" for s, e in right.keys() - left.keys())
    missing_provider = sorted(f"{s}:{e}" for s, e in left.keys() - right.keys())
    mismatches: list[dict[str, Any]] = []
    matched_net_minor: dict[str, int] = {}
    for key in sorted(left.keys() & right.keys()):
        local = left[key]
        remote = right[key]
        compared = ("gross_minor", "fee_minor", "currency", "status")
        differences = {
            field: {
                "internal": getattr(local, field),
                "provider": getattr(remote, field),
            }
            for field in compared
            if getattr(local, field) != getattr(remote, field)
        }
        if differences:
            mismatches.append(
                {
                    "event": f"{key[0]}:{key[1]}",
                    "differences": differences,
                }
            )
        else:
            matched_net_minor[local.currency] = (
                matched_net_minor.get(local.currency, 0) + local.net_minor
            )
    body = {
        "matched": len(left.keys() & right.keys()) - len(mismatches),
        "missing_internal": missing_internal,
        "missing_provider": missing_provider,
        "mismatches": mismatches,
        "internal_duplicates": internal_duplicates,
        "provider_duplicates": provider_duplicates,
        "matched_net_minor_by_currency": dict(sorted(matched_net_minor.items())),
    }
    return body | {
        "balanced": not any(
            (
                missing_internal,
                missing_provider,
                mismatches,
                internal_duplicates,
                provider_duplicates,
            )
        ),
        "reconciliation_hash": digest_payload(body),
        "non_claim": "reconciliation is an integrity aid, not a bank statement or tax filing",
    }
