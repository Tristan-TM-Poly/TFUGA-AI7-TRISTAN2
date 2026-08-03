from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Iterable

from .canonical import sha256_hex


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    source_id: str
    authority: str
    captured_on: str
    coverage: str
    records: tuple[int, ...]
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["records"] = list(self.records)
        payload["sha256"] = sha256_hex(payload)
        return payload


@dataclass(frozen=True, slots=True)
class PrecedenceReceipt:
    value: int
    status: str
    matching_sources: tuple[str, ...]
    checked_sources: tuple[str, ...]
    authoritative_sources: int
    coverage_complete_for_claim: bool
    scoped_absence_claim_allowed: bool
    global_novelty_claim_allowed: bool
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_precedence(
    value: int,
    snapshots: Iterable[SourceSnapshot],
    *,
    required_authoritative_sources: int = 2,
    complete_coverage_token: str = "exact-complete",
) -> PrecedenceReceipt:
    items = tuple(snapshots)
    matches = tuple(snapshot.source_id for snapshot in items if value in snapshot.records)
    checked = tuple(snapshot.source_id for snapshot in items)
    authoritative = sum(snapshot.authority == "authoritative" for snapshot in items)
    complete = bool(items) and all(snapshot.coverage == complete_coverage_token for snapshot in items)
    limitations: list[str] = []
    if not items:
        limitations.append("no source snapshots supplied")
    if authoritative < required_authoritative_sources:
        limitations.append("insufficient independent authoritative sources")
    if not complete:
        limitations.append("snapshot coverage does not establish global absence")
    if matches:
        status = "known-in-snapshot"
    elif items:
        status = "not-found-in-snapshots"
    else:
        status = "unchecked"
    scoped_absence_allowed = (
        not matches
        and authoritative >= required_authoritative_sources
        and complete
        and all(_valid_date(snapshot.captured_on) for snapshot in items)
    )
    if not scoped_absence_allowed:
        limitations.append("novelty claim remains prohibited")
    return PrecedenceReceipt(
        value=value,
        status=status,
        matching_sources=matches,
        checked_sources=checked,
        authoritative_sources=authoritative,
        coverage_complete_for_claim=complete,
        scoped_absence_claim_allowed=scoped_absence_allowed,
        global_novelty_claim_allowed=False,
        limitations=tuple(dict.fromkeys(limitations)),
    )


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
