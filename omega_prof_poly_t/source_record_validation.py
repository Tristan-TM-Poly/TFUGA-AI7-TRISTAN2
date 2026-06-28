"""Source record validation for Omega absorb v0.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .public_source_registry import PublicSourceRegistry, default_public_source_registry


@dataclass(frozen=True)
class RecordValidationFinding:
    record_id: str
    source_id: str
    level: str
    field: str
    message: str


@dataclass(frozen=True)
class RecordValidationReport:
    findings: Tuple[RecordValidationFinding, ...]
    valid_count: int
    invalid_count: int
    next_action: str

    @property
    def is_clean(self) -> bool:
        return self.invalid_count == 0


def validate_public_records(
    records: Iterable[Dict[str, object]],
    registry: PublicSourceRegistry | None = None,
    default_source_id: str = "demo_fixture",
) -> RecordValidationReport:
    registry = registry or default_public_source_registry()
    sources = registry.as_dict()
    findings = []
    valid_count = 0
    invalid_count = 0
    for index, record in enumerate(records, start=1):
        source_id = str(record.get("source_id") or record.get("source") or default_source_id)
        record_id = str(record.get("atom_id") or record.get("id") or record.get("identifier") or f"record-{index}")
        source = sources.get(source_id) or sources.get(default_source_id)
        allowed = set(source.allowed_fields if source else ())
        record_fields = set(str(key) for key in record.keys())
        allowed_extra = {"source", "source_id", "atom_id", "id", "identifier"}
        extra = sorted(record_fields - allowed - allowed_extra)
        missing_title = not (record.get("title") or record.get("dc.title") or record.get("name"))
        if extra:
            invalid_count += 1
            for field in extra:
                findings.append(
                    RecordValidationFinding(record_id, source_id, "warning", field, "field_not_in_allowed_registry")
                )
        elif missing_title:
            invalid_count += 1
            findings.append(RecordValidationFinding(record_id, source_id, "error", "title", "missing_title_like_field"))
        else:
            valid_count += 1
    return RecordValidationReport(
        findings=tuple(findings),
        valid_count=valid_count,
        invalid_count=invalid_count,
        next_action="normalize_valid_records_and_route_findings",
    )
