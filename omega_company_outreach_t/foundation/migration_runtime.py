from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .canonical import CanonicalizationError, canonical_mapping, normalize_text
from .contacts import RoleCategory
from .consent import ConsentBasis, ConsentScope
from .migration import MigratedCase, MigrationIds, migrate_outreach_case
from .opportunities import OpportunityType, StrategicSignals
from .organizations import OrganizationType


def migration_to_mapping(migrated: MigratedCase) -> dict[str, Any]:
    return canonical_mapping(
        {
            "schema_version": "1.0",
            "migration": "r0.2-to-r1.0",
            "source_case_hash": migrated.source_case_hash,
            "migration_hash": migrated.migration_hash,
            "organization": migrated.organization,
            "contact": migrated.contact,
            "consent": migrated.consent,
            "opportunity": migrated.opportunity,
            "events": [event.stored_mapping() for event in migrated.events],
        }
    )


def _resolve_organization_name(
    payload: Mapping[str, Any], organization_name: str | None
) -> dict[str, Any]:
    """Resolve a public organization name without guessing.

    Early R0.2 cases contained ``target_organization``. Later privacy-hardening
    removed that field while keeping only hashes. Migration therefore accepts
    an explicit public name supplied by the audited workflow. If both forms are
    present they must agree exactly after whitespace normalization.
    """

    normalized_payload = dict(payload)
    stored = payload.get("target_organization")
    stored_name = normalize_text(stored) if isinstance(stored, str) and stored.strip() else None
    supplied_name = normalize_text(organization_name) if organization_name else None
    if stored_name and supplied_name and stored_name != supplied_name:
        raise CanonicalizationError(
            "explicit organization name conflicts with legacy target_organization"
        )
    resolved = stored_name or supplied_name
    if not resolved:
        raise CanonicalizationError(
            "legacy case omits target_organization; provide an explicit organization_name"
        )
    normalized_payload["target_organization"] = resolved
    return normalized_payload


def migrate_case_file(
    source: Path,
    destination: Path,
    *,
    ids: MigrationIds,
    organization_type: OrganizationType,
    opportunity_type: OpportunityType,
    role_category: RoleCategory,
    consent_basis: ConsentBasis,
    consent_scope: ConsentScope,
    strategic_signals: StrategicSignals,
    proposed_asset_id: str,
    organization_domain: str | None = None,
    organization_name: str | None = None,
) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise CanonicalizationError("migration source file must contain an object")
    resolved_payload = _resolve_organization_name(payload, organization_name)
    migrated = migrate_outreach_case(
        resolved_payload,
        ids=ids,
        organization_type=organization_type,
        opportunity_type=opportunity_type,
        role_category=role_category,
        consent_basis=consent_basis,
        consent_scope=consent_scope,
        strategic_signals=strategic_signals,
        proposed_asset_id=proposed_asset_id,
        organization_domain=organization_domain,
    )
    output = migration_to_mapping(migrated)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return output


def audit_migration_bundle(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "migration",
        "source_case_hash",
        "migration_hash",
        "organization",
        "contact",
        "consent",
        "opportunity",
        "events",
    }
    missing = required - set(payload)
    if missing:
        errors.append(f"migration bundle missing fields: {sorted(missing)}")
    if payload.get("schema_version") != "1.0":
        errors.append("unsupported migration schema_version")
    if payload.get("migration") != "r0.2-to-r1.0":
        errors.append("unsupported migration type")
    events = payload.get("events")
    if not isinstance(events, list) or not events:
        errors.append("migration bundle requires events")
    return errors
