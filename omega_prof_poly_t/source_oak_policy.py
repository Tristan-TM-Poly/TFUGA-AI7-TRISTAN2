"""Source-specific OAK policies for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .source_registry_schema import SourceSchemaReport, validate_records_against_schema


@dataclass(frozen=True)
class SourceOAKPolicy:
    source_id: str
    allowed_fields: Tuple[str, ...]
    warning_rules: Tuple[str, ...]
    block_rules: Tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class SourceOAKPolicyReport:
    source_id: str
    status: str
    warnings: Tuple[str, ...]
    blocked_fields: Tuple[str, ...]
    schema_report: SourceSchemaReport
    next_action: str


def default_source_oak_policies() -> Dict[str, SourceOAKPolicy]:
    return {
        "generic": SourceOAKPolicy(
            "generic",
            ("title", "authors", "year", "abstract", "keywords", "claims", "methods", "limitations"),
            ("weak_provenance", "missing_methods"),
            ("restricted_field_present",),
            "normalize_to_research_atoms",
        ),
        "polypublie": SourceOAKPolicy(
            "polypublie",
            ("dc.title", "dc.creator", "dc.date", "dc.subject", "abstract", "link", "claims", "methods"),
            ("missing_methods", "missing_limitations"),
            ("restricted_field_present",),
            "normalize_to_research_atoms",
        ),
        "expertise": SourceOAKPolicy(
            "expertise",
            ("name", "expertise", "department", "methods", "claims"),
            ("public_profile_scope", "inference_limit"),
            ("restricted_field_present",),
            "normalize_to_research_atoms",
        ),
    }


def apply_source_oak_policy(records: Iterable[Dict[str, object]], source_id: str = "generic") -> SourceOAKPolicyReport:
    policies = default_source_oak_policies()
    policy = policies.get(source_id, policies["generic"])
    schema = validate_records_against_schema(records, source_id if source_id in {"generic", "polypublie", "expertise"} else "generic")
    blocked = tuple(finding.field for finding in schema.findings if finding.level == "blocked")
    warnings = tuple(finding.message for finding in schema.findings if finding.level in {"warning", "error"})
    if blocked:
        status = "blocked"
    elif warnings:
        status = "allow_with_warnings"
    else:
        status = "allow"
    return SourceOAKPolicyReport(
        source_id=policy.source_id,
        status=status,
        warnings=warnings,
        blocked_fields=blocked,
        schema_report=schema,
        next_action=policy.next_action if status != "blocked" else "stop_before_absorption",
    )
