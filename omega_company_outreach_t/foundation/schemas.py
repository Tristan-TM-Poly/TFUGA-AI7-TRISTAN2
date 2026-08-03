from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import CanonicalizationError, canonical_hash


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    version: str
    schema: Mapping[str, Any]

    @property
    def schema_id(self) -> str:
        return f"https://schemas.tristan.local/company-outreach/{self.name}/{self.version}"

    @property
    def schema_hash(self) -> str:
        return canonical_hash(self.schema)

    def as_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "schema_id": self.schema_id,
            "schema_hash": self.schema_hash,
            "schema": dict(self.schema),
        }


def _object_schema(
    *,
    title: str,
    required: Iterable[str],
    properties: Mapping[str, Any],
    additional_properties: bool = False,
) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": additional_properties,
    }


def _identifier(prefix: str) -> dict[str, Any]:
    return {
        "type": "string",
        "pattern": rf"^{prefix}-[0-9]{{4}}-[0-9]{{4,12}}$",
    }


def _sha256() -> dict[str, Any]:
    return {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}


def _hmac_or_sha256() -> dict[str, Any]:
    return {
        "type": "string",
        "pattern": "^(?:sha256|hmac-sha256):[0-9a-f]{64}$",
    }


def _datetime() -> dict[str, Any]:
    return {"type": "string", "format": "date-time"}


def schema_definitions() -> tuple[SchemaDefinition, ...]:
    string_map = {
        "type": "object",
        "additionalProperties": {"type": "string", "maxLength": 1000},
    }
    hash_array = {"type": "array", "items": _sha256(), "uniqueItems": True}
    definitions = (
        SchemaDefinition(
            "company-identity",
            "1.0",
            _object_schema(
                title="Company Identity",
                required=["company_id", "display_name", "state", "purpose"],
                properties={
                    "company_id": {"type": "string", "pattern": "^tristan_[a-z0-9_]+$"},
                    "display_name": {"type": "string", "minLength": 1, "maxLength": 240},
                    "state": {
                        "enum": [
                            "concept",
                            "internal_role",
                            "brand_candidate",
                            "domain_verified",
                            "legal_entity_verified",
                            "banking_verified",
                            "tax_verified",
                            "contract_ready",
                            "production_company",
                        ]
                    },
                    "purpose": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1, "maxLength": 240},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "domains": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/domainClaim"},
                        "uniqueItems": True,
                    },
                    "legal_entity": {"$ref": "#/$defs/legalEntity"},
                    "authenticated_sender_type": {"type": "string", "maxLength": 100},
                    "external_commitment_allowed": {"type": "boolean"},
                    "metadata": string_map,
                },
            )
            | {
                "$defs": {
                    "domainClaim": _object_schema(
                        title="Domain Claim",
                        required=["domain", "verified"],
                        properties={
                            "domain": {"type": "string", "format": "hostname"},
                            "verified": {"type": "boolean"},
                            "verification_method": {"type": ["string", "null"]},
                            "evidence_hash": {"anyOf": [_sha256(), {"type": "null"}]},
                            "verified_at": {"anyOf": [_datetime(), {"type": "null"}]},
                        },
                    ),
                    "legalEntity": _object_schema(
                        title="Legal Entity Evidence",
                        required=[
                            "jurisdiction",
                            "legal_name",
                            "registration_hash",
                            "verified_at",
                            "verifier_role",
                        ],
                        properties={
                            "jurisdiction": {"type": "string", "maxLength": 24},
                            "legal_name": {"type": "string", "maxLength": 240},
                            "registration_hash": _sha256(),
                            "verified_at": _datetime(),
                            "verifier_role": {"type": "string"},
                        },
                    ),
                }
            },
        ),
        SchemaDefinition(
            "authority-grant",
            "1.0",
            _object_schema(
                title="Authority Grant",
                required=[
                    "grant_id",
                    "person_id",
                    "company_id",
                    "role",
                    "permissions",
                    "valid_from",
                    "valid_until",
                    "evidence_hash",
                ],
                properties={
                    "grant_id": _identifier("AUTH"),
                    "person_id": {"type": "string", "minLength": 1, "maxLength": 200},
                    "company_id": {"type": "string", "pattern": "^tristan_[a-z0-9_]+$"},
                    "role": {"type": "string"},
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "valid_from": _datetime(),
                    "valid_until": _datetime(),
                    "evidence_hash": _sha256(),
                    "amount_limit_cad": {"type": ["integer", "null"], "minimum": 0},
                    "jurisdictions": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 24},
                        "uniqueItems": True,
                    },
                    "revoked_at": {"anyOf": [_datetime(), {"type": "null"}]},
                },
            ),
        ),
        SchemaDefinition(
            "organization",
            "1.0",
            _object_schema(
                title="Organization",
                required=[
                    "organization_id",
                    "canonical_name",
                    "organization_type",
                    "country",
                    "relationship_state",
                ],
                properties={
                    "organization_id": _identifier("ORG"),
                    "canonical_name": {"type": "string", "minLength": 1, "maxLength": 240},
                    "organization_type": {"type": "string"},
                    "country": {"type": "string", "minLength": 2, "maxLength": 3},
                    "region": {"type": ["string", "null"], "maxLength": 24},
                    "domains": {
                        "type": "array",
                        "items": {"type": "string", "format": "hostname"},
                        "uniqueItems": True,
                    },
                    "aliases": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 240},
                        "uniqueItems": True,
                    },
                    "strategic_roles": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 100},
                        "uniqueItems": True,
                    },
                    "evidence": {"type": "array", "items": {"type": "object"}},
                    "divisions": {"type": "array", "items": {"type": "object"}},
                    "relationship_state": {"type": "string"},
                    "metadata": string_map,
                },
            ),
        ),
        SchemaDefinition(
            "contact-record",
            "1.0",
            _object_schema(
                title="Privacy-preserving Contact Record",
                required=[
                    "contact_id",
                    "organization_id",
                    "role_category",
                    "state",
                    "recipient_hash",
                    "private_email_ref",
                ],
                properties={
                    "contact_id": _identifier("CNT"),
                    "organization_id": _identifier("ORG"),
                    "role_category": {"type": "string"},
                    "state": {"type": "string"},
                    "recipient_hash": _hmac_or_sha256(),
                    "private_email_ref": {"type": "string", "pattern": "^vault://"},
                    "private_name_ref": {
                        "anyOf": [
                            {"type": "string", "pattern": "^vault://"},
                            {"type": "null"},
                        ]
                    },
                    "title": {"type": ["string", "null"], "maxLength": 240},
                    "department": {"type": ["string", "null"], "maxLength": 240},
                    "domain": {"type": ["string", "null"]},
                    "sources": {"type": "array", "items": {"type": "object"}},
                    "preferences": {"type": "object"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 100},
                        "uniqueItems": True,
                    },
                    "created_at": _datetime(),
                    "updated_at": _datetime(),
                    "metadata": string_map,
                },
            ),
        ),
        SchemaDefinition(
            "consent-record",
            "1.0",
            _object_schema(
                title="Consent Record",
                required=[
                    "consent_id",
                    "contact_id",
                    "basis",
                    "scopes",
                    "state",
                    "obtained_at",
                    "evidence_hash",
                ],
                properties={
                    "consent_id": _identifier("CONSENT"),
                    "contact_id": _identifier("CNT"),
                    "basis": {"type": "string"},
                    "scopes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "state": {"type": "string"},
                    "obtained_at": _datetime(),
                    "evidence_hash": _sha256(),
                    "expires_at": {"anyOf": [_datetime(), {"type": "null"}]},
                    "withdrawn_at": {"anyOf": [_datetime(), {"type": "null"}]},
                    "notes_hash": {"anyOf": [_sha256(), {"type": "null"}]},
                    "metadata": string_map,
                },
            ),
        ),
        SchemaDefinition(
            "suppression-entry",
            "1.0",
            _object_schema(
                title="Suppression Entry",
                required=[
                    "suppression_id",
                    "contact_id",
                    "reason",
                    "created_at",
                    "evidence_hash",
                    "permanent",
                    "scopes",
                ],
                properties={
                    "suppression_id": _identifier("SUPPRESS"),
                    "contact_id": _identifier("CNT"),
                    "organization_id": {"anyOf": [_identifier("ORG"), {"type": "null"}]},
                    "reason": {"type": "string"},
                    "created_at": _datetime(),
                    "evidence_hash": _sha256(),
                    "permanent": {"type": "boolean"},
                    "expires_at": {"anyOf": [_datetime(), {"type": "null"}]},
                    "scopes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
            ),
        ),
        SchemaDefinition(
            "opportunity",
            "1.0",
            _object_schema(
                title="Strategic Opportunity",
                required=[
                    "opportunity_id",
                    "organization_id",
                    "company_unit",
                    "opportunity_type",
                    "state",
                    "problem_statement",
                    "proposed_asset_id",
                    "evidence_hashes",
                    "signals",
                ],
                properties={
                    "opportunity_id": _identifier("OPP"),
                    "organization_id": _identifier("ORG"),
                    "contact_id": {"anyOf": [_identifier("CNT"), {"type": "null"}]},
                    "company_unit": {"type": "string", "pattern": "^tristan_[a-z0-9_]+$"},
                    "opportunity_type": {"type": "string"},
                    "state": {"type": "string"},
                    "problem_statement": {"type": "string", "minLength": 1, "maxLength": 3000},
                    "proposed_asset_id": {"type": "string", "minLength": 1},
                    "evidence_hashes": hash_array,
                    "signals": {"type": "object"},
                    "posterior": {"type": "object"},
                    "source_issue": {"type": ["integer", "null"], "minimum": 1},
                    "estimated_effort_hours": {"type": "number", "exclusiveMinimum": 0},
                    "expected_value_cad": {"type": ["integer", "null"], "minimum": 0},
                    "created_at": _datetime(),
                    "updated_at": _datetime(),
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "metadata": string_map,
                },
            ),
        ),
        SchemaDefinition(
            "domain-event",
            "1.0",
            _object_schema(
                title="Append-only Domain Event",
                required=[
                    "event_id",
                    "event_type",
                    "aggregate_type",
                    "aggregate_id",
                    "sequence",
                    "occurred_at",
                    "actor",
                    "payload",
                    "event_hash",
                ],
                properties={
                    "event_id": _identifier("EVT"),
                    "event_type": {"type": "string"},
                    "aggregate_type": {"type": "string"},
                    "aggregate_id": {"type": "string", "minLength": 1},
                    "sequence": {"type": "integer", "minimum": 1},
                    "occurred_at": _datetime(),
                    "actor": {"type": "object"},
                    "payload": {"type": "object"},
                    "previous_hash": {"anyOf": [_sha256(), {"type": "null"}]},
                    "correlation_id": {
                        "anyOf": [_identifier("CORR"), {"type": "null"}]
                    },
                    "causation_id": {"anyOf": [_identifier("EVT"), {"type": "null"}]},
                    "idempotency_key": {
                        "anyOf": [_hmac_or_sha256(), {"type": "null"}]
                    },
                    "schema_version": {"type": "string", "maxLength": 32},
                    "event_hash": _sha256(),
                },
            ),
        ),
        SchemaDefinition(
            "graph-node",
            "1.0",
            _object_schema(
                title="Relationship Graph Node",
                required=["node_id", "node_type", "label", "public_attributes", "version"],
                properties={
                    "node_id": {"type": "string", "minLength": 1},
                    "node_type": {"type": "string"},
                    "label": {"type": "string", "minLength": 1},
                    "public_attributes": {"type": "object"},
                    "private_reference_hashes": hash_array,
                    "evidence_hashes": hash_array,
                    "version": {"type": "integer", "minimum": 1},
                    "node_hash": _sha256(),
                },
            ),
        ),
        SchemaDefinition(
            "graph-edge",
            "1.0",
            _object_schema(
                title="Relationship Graph Edge",
                required=[
                    "edge_id",
                    "edge_type",
                    "source_id",
                    "target_id",
                    "weight",
                    "confidence",
                ],
                properties={
                    "edge_id": {"type": "string", "minLength": 1},
                    "edge_type": {"type": "string"},
                    "source_id": {"type": "string", "minLength": 1},
                    "target_id": {"type": "string", "minLength": 1},
                    "weight": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence_hashes": hash_array,
                    "attributes": {"type": "object"},
                    "edge_hash": _sha256(),
                },
            ),
        ),
        SchemaDefinition(
            "oak-scenario",
            "1.0",
            _object_schema(
                title="OAK Scenario",
                required=["scenario_id", "dimensions", "expectation", "generator_version", "scenario_hash"],
                properties={
                    "scenario_id": {"type": "string", "pattern": "^SCENARIO-[0-9]{8}$"},
                    "dimensions": {"type": "object"},
                    "expectation": {"type": "object"},
                    "generator_version": {"type": "string"},
                    "scenario_hash": _sha256(),
                },
            ),
        ),
        SchemaDefinition(
            "migration-bundle",
            "1.0",
            _object_schema(
                title="R0.2 to R1.0 Migration Bundle",
                required=[
                    "schema_version",
                    "migration",
                    "source_case_hash",
                    "migration_hash",
                    "organization",
                    "contact",
                    "consent",
                    "opportunity",
                    "events",
                ],
                properties={
                    "schema_version": {"const": "1.0"},
                    "migration": {"const": "r0.2-to-r1.0"},
                    "source_case_hash": _sha256(),
                    "migration_hash": _sha256(),
                    "organization": {"type": "object"},
                    "contact": {"type": "object"},
                    "consent": {"type": "object"},
                    "opportunity": {"type": "object"},
                    "events": {"type": "array", "items": {"type": "object"}, "minItems": 1},
                },
            ),
        ),
    )
    return definitions


def schema_catalog() -> dict[str, Any]:
    definitions = schema_definitions()
    return {
        "schema_version": "1.0",
        "namespace": "omega-company-outreach-foundation",
        "schemas": [definition.as_mapping() for definition in definitions],
        "schema_count": len(definitions),
        "catalog_hash": canonical_hash(
            [(definition.name, definition.version, definition.schema_hash) for definition in definitions]
        ),
    }


def write_schema_catalog(directory: Path) -> dict[str, Any]:
    catalog = schema_catalog()
    directory.mkdir(parents=True, exist_ok=True)
    for definition in schema_definitions():
        path = directory / f"{definition.name}.v{definition.version}.schema.json"
        payload = dict(definition.schema)
        payload["$id"] = definition.schema_id
        payload["x-schema-hash"] = definition.schema_hash
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
    (directory / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return catalog


def audit_schema_catalog(directory: Path) -> list[str]:
    errors: list[str] = []
    catalog_path = directory / "catalog.json"
    if not catalog_path.exists():
        return ["schema catalog is missing"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    expected = schema_catalog()
    if catalog.get("schema_count") != expected["schema_count"]:
        errors.append("schema_count mismatch")
    if catalog.get("catalog_hash") != expected["catalog_hash"]:
        errors.append("catalog_hash mismatch")
    for definition in schema_definitions():
        path = directory / f"{definition.name}.v{definition.version}.schema.json"
        if not path.exists():
            errors.append(f"missing schema file: {path.name}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        stored_hash = payload.pop("x-schema-hash", None)
        payload.pop("$id", None)
        if stored_hash != definition.schema_hash:
            errors.append(f"stored schema hash mismatch: {definition.name}")
        if canonical_hash(payload) != definition.schema_hash:
            errors.append(f"schema content mismatch: {definition.name}")
    return errors
