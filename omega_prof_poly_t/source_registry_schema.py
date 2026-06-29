"""Strict source registry schema for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


RESTRICTED_FIELDS = (
    "full_text",
    "pdf_text",
    "private_email",
    "student_id",
    "phone",
    "secret",
    "token",
    "password",
)


@dataclass(frozen=True)
class SourceSchema:
    source_id: str
    allowed_fields: Tuple[str, ...]
    required_fields: Tuple[str, ...]
    restricted_fields: Tuple[str, ...]
    adapter: str
    risk_level: str
    policy: str
    oak_action: str


@dataclass(frozen=True)
class SourceSchemaFinding:
    record_id: str
    source_id: str
    field: str
    level: str
    message: str


@dataclass(frozen=True)
class SourceSchemaReport:
    findings: Tuple[SourceSchemaFinding, ...]
    accepted_count: int
    rejected_count: int
    next_action: str

    @property
    def is_clean(self) -> bool:
        return self.rejected_count == 0 and not self.findings


def default_source_schemas() -> Dict[str, SourceSchema]:
    common = ("atom_id", "id", "identifier", "title", "dc.title", "name", "authors", "creators", "dc.creator", "year", "date", "dc.date", "source", "source_id", "link", "url", "abstract", "description", "dc.description", "keywords", "subjects", "dc.subject", "departments", "department", "division", "professors", "directors", "supervisors", "claims", "methods", "limitations", "datasets", "code_links")
    return {
        "generic": SourceSchema("generic", common, ("title",), RESTRICTED_FIELDS, "GenericPublicMetadataAdapter", "low", "metadata_only", "allow_metadata_absorption"),
        "polypublie": SourceSchema("polypublie", common, ("dc.title",), RESTRICTED_FIELDS, "PolyPublieLikeAdapter", "low", "metadata_and_abstract", "allow_public_metadata_absorption"),
        "expertise": SourceSchema("expertise", common, ("name",), RESTRICTED_FIELDS, "ExpertiseLikeAdapter", "low", "profile_metadata", "allow_profile_metadata_absorption"),
    }


def validate_records_against_schema(records: Iterable[Dict[str, object]], source_id: str = "generic") -> SourceSchemaReport:
    schemas = default_source_schemas()
    schema = schemas.get(source_id, schemas["generic"])
    findings = []
    accepted = 0
    rejected = 0
    allowed = set(schema.allowed_fields)
    restricted = set(schema.restricted_fields)
    for index, record in enumerate(records, start=1):
        record_id = str(record.get("atom_id") or record.get("id") or record.get("identifier") or f"record-{index}")
        keys = set(str(key) for key in record.keys())
        restricted_hits = sorted(keys & restricted)
        unknown_hits = sorted(keys - allowed - restricted)
        missing = [field for field in schema.required_fields if field not in keys]
        if restricted_hits or missing:
            rejected += 1
        else:
            accepted += 1
        for field in restricted_hits:
            findings.append(SourceSchemaFinding(record_id, source_id, field, "blocked", "restricted_field_present"))
        for field in missing:
            findings.append(SourceSchemaFinding(record_id, source_id, field, "error", "required_field_missing"))
        for field in unknown_hits:
            findings.append(SourceSchemaFinding(record_id, source_id, field, "warning", "field_not_in_schema"))
    return SourceSchemaReport(tuple(findings), accepted, rejected, "route_schema_findings")
