from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import CanonicalizationError, canonical_hash, is_sha256, normalize_text
from .contacts import (
    ContactEvidence,
    ContactPreferences,
    ContactRecord,
    ContactSource,
    ContactState,
    RoleCategory,
)
from .consent import ConsentBasis, ConsentRecord, ConsentScope, ConsentState
from .events import AggregateType, DomainEvent, EventActor, EventType, audit_event_sequence
from .organizations import (
    EvidenceKind,
    Organization,
    OrganizationEvidence,
    OrganizationType,
    RelationshipState,
)
from .opportunities import (
    CompanyUnit,
    Opportunity,
    OpportunityState,
    OpportunityType,
    StrategicSignals,
)


@dataclass(frozen=True, slots=True)
class MigrationIds:
    organization_id: str
    contact_id: str
    consent_id: str
    opportunity_id: str
    evidence_id: str
    contact_evidence_id: str
    event_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MigratedCase:
    organization: Organization
    contact: ContactRecord
    consent: ConsentRecord
    opportunity: Opportunity
    events: tuple[DomainEvent, ...]
    source_case_hash: str

    @property
    def migration_hash(self) -> str:
        return canonical_hash(
            {
                "organization_hash": self.organization.organization_hash,
                "contact_hash": self.contact.contact_hash,
                "consent_hash": self.consent.consent_hash,
                "opportunity_hash": self.opportunity.opportunity_hash,
                "event_hashes": [event.event_hash for event in self.events],
                "source_case_hash": self.source_case_hash,
            }
        )


def _parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if len(raw) == 10:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not normalize_text(value):
        raise CanonicalizationError(f"migration source requires string field {key}")
    return normalize_text(value)


def _source_case_hash(payload: Mapping[str, Any]) -> str:
    return canonical_hash(dict(payload))


def migrate_outreach_case(
    payload: Mapping[str, Any],
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
) -> MigratedCase:
    case_id = _required_string(payload, "case_id")
    target_organization = _required_string(payload, "target_organization")
    recipient_hash = _required_string(payload, "recipient_hash")
    provider_receipt_hash = _required_string(payload, "provider_receipt_hash")
    purpose = _required_string(payload, "purpose")
    sent_at = _parse_datetime(_required_string(payload, "sent_at"))
    source_issue = payload.get("source_issue")
    if not isinstance(source_issue, int) or source_issue < 1:
        raise CanonicalizationError("migration source requires a positive source_issue")
    if not is_sha256(recipient_hash):
        raise CanonicalizationError("legacy recipient_hash must be canonical SHA-256")
    if not is_sha256(provider_receipt_hash):
        raise CanonicalizationError("legacy provider_receipt_hash must be canonical SHA-256")
    if bool(payload.get("legal_entity_claimed")):
        raise CanonicalizationError("legacy case with legal entity claim requires manual migration")
    source_hash = _source_case_hash(payload)
    organization_evidence = OrganizationEvidence(
        evidence_id=ids.evidence_id,
        kind=EvidenceKind.EXISTING_RELATIONSHIP,
        source_hash=source_hash,
        observed_at=sent_at,
        claim=f"Existing external outreach case {case_id} targets this organization.",
        confidence=0.90,
        official=False,
    )
    organization = Organization(
        organization_id=ids.organization_id,
        canonical_name=target_organization,
        organization_type=organization_type,
        country="CA",
        region="QC",
        domains=(organization_domain,) if organization_domain else (),
        strategic_roles=(opportunity_type.value,),
        evidence=(organization_evidence,),
        relationship_state=RelationshipState.CONTACTED,
        metadata={"source_case": case_id, "source_issue": str(source_issue)},
    )
    contact_evidence = ContactEvidence(
        evidence_id=ids.contact_evidence_id,
        source=ContactSource.EXISTING_RELATIONSHIP,
        source_hash=provider_receipt_hash,
        observed_at=sent_at,
        organization_domain=organization_domain,
        role_verified=role_category is not RoleCategory.UNKNOWN,
        relationship_verified=True,
        confidence=0.85,
    )
    contact = ContactRecord(
        contact_id=ids.contact_id,
        organization_id=ids.organization_id,
        role_category=role_category,
        state=ContactState.CONTACTED,
        recipient_hash=recipient_hash,
        private_email_ref=f"vault://company-outreach/contacts/{ids.contact_id}/email",
        private_name_ref=None,
        domain=organization_domain,
        sources=(contact_evidence,),
        preferences=ContactPreferences(
            language="fr",
            preferred_channel="email",
            no_marketing=False,
            no_follow_up=False,
            maximum_messages_per_30_days=2,
        ),
        tags=("migrated-r0.2", opportunity_type.value),
        created_at=sent_at,
        updated_at=sent_at,
        metadata={"source_case": case_id},
    )
    consent = ConsentRecord(
        consent_id=ids.consent_id,
        contact_id=ids.contact_id,
        basis=consent_basis,
        scopes=frozenset({consent_scope, ConsentScope.DIRECT_INDIVIDUAL_CONTACT}),
        state=ConsentState.VALID,
        obtained_at=sent_at,
        evidence_hash=source_hash,
        metadata={"source_case": case_id, "migration": "r0.2-to-r1.0"},
    )
    company_unit = CompanyUnit(_required_string(payload, "company_unit"))
    opportunity = Opportunity(
        opportunity_id=ids.opportunity_id,
        organization_id=ids.organization_id,
        company_unit=company_unit,
        opportunity_type=opportunity_type,
        state=OpportunityState.ACTIVE,
        problem_statement=purpose,
        proposed_asset_id=proposed_asset_id,
        evidence_hashes=(source_hash, provider_receipt_hash),
        signals=strategic_signals,
        contact_id=ids.contact_id,
        source_issue=source_issue,
        estimated_effort_hours=4.0,
        created_at=sent_at,
        updated_at=sent_at,
        tags=("migrated-r0.2",),
        metadata={"source_case": case_id},
    )
    actor = EventActor(
        actor_id="tristan",
        actor_type="founder",
        company_id=company_unit.value,
    )
    correlation_id = f"CORR-{sent_at.year}-{int(case_id.rsplit('-', 1)[-1]):04d}"
    event_specs = (
        (
            EventType.ORGANIZATION_DISCOVERED,
            AggregateType.ORGANIZATION,
            ids.organization_id,
            {
                "projection": {
                    "canonical_name": organization.canonical_name,
                    "organization_type": organization.organization_type.value,
                    "relationship_state": organization.relationship_state.value,
                },
                "organization_hash": organization.organization_hash,
            },
        ),
        (
            EventType.CONTACT_VERIFIED,
            AggregateType.CONTACT,
            ids.contact_id,
            {
                "projection": {
                    "organization_id": ids.organization_id,
                    "role_category": role_category.value,
                    "state": contact.state.value,
                },
                "contact_hash": contact.contact_hash,
            },
        ),
        (
            EventType.CONSENT_RECORDED,
            AggregateType.CONSENT,
            ids.consent_id,
            {
                "projection": {
                    "contact_id": ids.contact_id,
                    "basis": consent_basis.value,
                    "state": consent.state.value,
                },
                "consent_hash": consent.consent_hash,
            },
        ),
        (
            EventType.OPPORTUNITY_CREATED,
            AggregateType.OPPORTUNITY,
            ids.opportunity_id,
            {
                "projection": {
                    "organization_id": ids.organization_id,
                    "company_unit": company_unit.value,
                    "opportunity_type": opportunity_type.value,
                    "state": opportunity.state.value,
                    "strategic_score": opportunity.strategic_score,
                },
                "opportunity_hash": opportunity.opportunity_hash,
            },
        ),
        (
            EventType.MESSAGE_SENT,
            AggregateType.OUTREACH_CASE,
            case_id,
            {
                "projection": {
                    "company_unit": company_unit.value,
                    "organization_id": ids.organization_id,
                    "contact_id": ids.contact_id,
                    "opportunity_id": ids.opportunity_id,
                    "state": "sent",
                },
                "provider_receipt_hash": provider_receipt_hash,
                "source_case_hash": source_hash,
            },
        ),
    )
    if len(ids.event_ids) != len(event_specs):
        raise CanonicalizationError("migration event_ids length does not match event plan")
    events: list[DomainEvent] = []
    aggregate_hashes: dict[tuple[AggregateType, str], str] = {}
    aggregate_sequences: dict[tuple[AggregateType, str], int] = {}
    for event_id, spec in zip(ids.event_ids, event_specs):
        event_type, aggregate_type, aggregate_id, event_payload = spec
        key = (aggregate_type, aggregate_id)
        sequence = aggregate_sequences.get(key, 0) + 1
        event = DomainEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            sequence=sequence,
            occurred_at=sent_at,
            actor=actor,
            payload=event_payload,
            previous_hash=aggregate_hashes.get(key),
            correlation_id=correlation_id,
            idempotency_key=canonical_hash(
                {"migration": "r0.2-to-r1.0", "case_id": case_id, "event": event_type.value}
            ),
        )
        events.append(event)
        aggregate_sequences[key] = sequence
        aggregate_hashes[key] = event.event_hash
    sequence_errors = audit_event_sequence(events)
    if sequence_errors:
        raise CanonicalizationError("invalid migration event sequence: " + "; ".join(sequence_errors))
    return MigratedCase(
        organization=organization,
        contact=contact,
        consent=consent,
        opportunity=opportunity,
        events=tuple(events),
        source_case_hash=source_hash,
    )


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
) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CanonicalizationError("migration source file must contain an object")
    migrated = migrate_outreach_case(
        payload,
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
    output = {
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2, default=str),
        encoding="utf-8",
    )
    return output


def audit_migrations(migrations: Iterable[MigratedCase]) -> list[str]:
    errors: list[str] = []
    seen_organizations: set[str] = set()
    seen_contacts: set[str] = set()
    seen_opportunities: set[str] = set()
    seen_event_ids: set[str] = set()
    for migration in migrations:
        if migration.organization.organization_id in seen_organizations:
            errors.append(
                f"duplicate migrated organization: {migration.organization.organization_id}"
            )
        seen_organizations.add(migration.organization.organization_id)
        if migration.contact.contact_id in seen_contacts:
            errors.append(f"duplicate migrated contact: {migration.contact.contact_id}")
        seen_contacts.add(migration.contact.contact_id)
        if migration.opportunity.opportunity_id in seen_opportunities:
            errors.append(
                f"duplicate migrated opportunity: {migration.opportunity.opportunity_id}"
            )
        seen_opportunities.add(migration.opportunity.opportunity_id)
        for event in migration.events:
            if event.event_id in seen_event_ids:
                errors.append(f"duplicate migration event: {event.event_id}")
            seen_event_ids.add(event.event_id)
    return errors
