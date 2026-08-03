"""Local-snapshot intake and provenance validation.

R0.2 deliberately does not scrape the network inside its core library. Network
collection belongs to source-specific jobs that save licensed snapshots first.
The intake layer consumes those snapshots, hashes them and emits conservative
ProblemLead records.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Iterable, Iterator

from .models import LeadStatus, ProblemLead, SourceSnapshot


_FORBIDDEN_FIELDS = {
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "bank_account",
    "transit_number",
    "institution_number",
    "tax_identifier",
}


@dataclass(frozen=True)
class IntakePolicy:
    source_id: str
    authority_class: str
    license_class: str
    allow_statement_summary: bool
    allow_full_statement: bool
    require_status_recheck: bool
    require_literature_check: bool
    max_summary_chars: int = 1200


@dataclass(frozen=True)
class IntakeReport:
    source_id: str
    record_count: int
    accepted_count: int
    rejected_count: int
    duplicate_locator_count: int
    snapshot_hash: str
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "record_count": self.record_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "duplicate_locator_count": self.duplicate_locator_count,
            "snapshot_hash": self.snapshot_hash,
            "findings": list(self.findings),
        }


def snapshot_file(path: str | Path, policy: IntakePolicy, retrieved_at: str) -> SourceSnapshot:
    raw = Path(path).read_bytes()
    return SourceSnapshot(
        source_id=policy.source_id,
        canonical_url=f"file://{Path(path).name}",
        retrieved_at=retrieved_at,
        content_sha256=sha256(raw).hexdigest(),
        license_class=policy.license_class,
        authority_class=policy.authority_class,
        status_policy=(
            "STATUS_RECHECK_REQUIRED"
            if policy.require_status_recheck
            else "SOURCE_STATUS_ACCEPTED_FOR_FIXTURE_ONLY"
        ),
        network_fetch_performed=False,
        notes=("local snapshot consumed; network collection is out of core scope",),
    )


def load_json_records(path: str | Path) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = payload["records"]
    else:
        raise ValueError("snapshot must be a list or an object with records[]")
    if not all(isinstance(item, dict) for item in records):
        raise ValueError("all records must be JSON objects")
    return list(records)


def audit_sensitive_fields(value: object, path: str = "$") -> tuple[str, ...]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
            if normalized in _FORBIDDEN_FIELDS:
                findings.append(f"forbidden sensitive field at {path}.{key}")
            findings.extend(audit_sensitive_fields(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(audit_sensitive_fields(child, f"{path}[{index}]"))
    return tuple(findings)


def ingest_records(
    records: Iterable[dict[str, object]],
    policy: IntakePolicy,
    snapshot: SourceSnapshot,
) -> tuple[tuple[ProblemLead, ...], IntakeReport]:
    materialized = tuple(records)
    findings: list[str] = list(audit_sensitive_fields(materialized))
    accepted: list[ProblemLead] = []
    locators: set[str] = set()
    duplicate_locators = 0
    rejected = 0
    for ordinal, raw in enumerate(materialized):
        locator = str(raw.get("source_locator", "")).strip()
        title = str(raw.get("title", "")).strip()
        summary = str(raw.get("statement_summary", raw.get("statement", ""))).strip()
        domains_raw = raw.get("domains", [])
        if not locator or not title or not summary or not isinstance(domains_raw, list):
            rejected += 1
            findings.append(f"record {ordinal}: missing locator/title/summary/domains")
            continue
        if locator in locators:
            duplicate_locators += 1
            rejected += 1
            findings.append(f"record {ordinal}: duplicate source locator {locator}")
            continue
        locators.add(locator)
        if len(summary) > policy.max_summary_chars:
            if policy.allow_statement_summary:
                summary = summary[: policy.max_summary_chars].rstrip() + "…"
                findings.append(f"record {ordinal}: summary truncated by policy")
            else:
                rejected += 1
                findings.append(f"record {ordinal}: summary storage prohibited")
                continue
        if not policy.allow_statement_summary:
            summary = "Metadata-only lead; consult cited source for the statement."
        status = (
            LeadStatus.STATUS_RECHECK_REQUIRED
            if policy.require_status_recheck
            else LeadStatus.SOURCE_REPORTED
        )
        accepted.append(
            ProblemLead(
                lead_id=str(raw.get("lead_id") or f"{policy.source_id}-{ordinal:08d}"),
                source_id=policy.source_id,
                source_locator=locator,
                title=title,
                statement_summary=summary,
                domains=tuple(sorted(str(item) for item in domains_raw)),
                kind=str(raw.get("kind", "RESEARCH_PROBLEM")),
                lead_status=status,
                source_snapshot_hash=snapshot.canonical_hash(),
                authors=tuple(str(item) for item in raw.get("authors", [])),
                citations=tuple(str(item) for item in raw.get("citations", [])),
                methods=tuple(str(item) for item in raw.get("methods", [])),
                last_status_check=None,
                license_reviewed=policy.license_class not in {"UNKNOWN", "REVIEW_REQUIRED"},
                literature_search_required=policy.require_literature_check,
                independently_checked_open=False,
                finite_computation_is_not_proof=True,
                solution_claimed=False,
                metadata={
                    "intake_ordinal": ordinal,
                    "source_authority": policy.authority_class,
                    "generated_fixture": bool(raw.get("generated_fixture", False)),
                },
            )
        )
    if findings and any("forbidden sensitive field" in item for item in findings):
        accepted = []
        rejected = len(materialized)
    report = IntakeReport(
        source_id=policy.source_id,
        record_count=len(materialized),
        accepted_count=len(accepted),
        rejected_count=rejected,
        duplicate_locator_count=duplicate_locators,
        snapshot_hash=snapshot.canonical_hash(),
        findings=tuple(findings),
    )
    return tuple(accepted), report


def jsonl(leads: Iterable[ProblemLead]) -> Iterator[str]:
    for lead in leads:
        payload = {
            "lead_id": lead.lead_id,
            "source_id": lead.source_id,
            "source_locator": lead.source_locator,
            "title": lead.title,
            "statement_summary": lead.statement_summary,
            "domains": list(lead.domains),
            "kind": lead.kind,
            "lead_status": lead.lead_status.value,
            "source_snapshot_hash": lead.source_snapshot_hash,
            "independently_checked_open": lead.independently_checked_open,
            "finite_computation_is_not_proof": lead.finite_computation_is_not_proof,
            "solution_claimed": lead.solution_claimed,
            "record_hash": lead.canonical_hash(),
        }
        yield json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
