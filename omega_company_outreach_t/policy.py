from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .models import CompanyUnit, OutreachCase, OutreachKind, OutreachStatus


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    unit: CompanyUnit
    display_name: str
    role: str
    legal_state: str
    verified_domain: bool
    allowed_kinds: frozenset[OutreachKind]


PROFILES = {
    CompanyUnit.PARENT: CompanyProfile(
        unit=CompanyUnit.PARENT,
        display_name="Tristan Parent OpCo",
        role="strategy, entrepreneurship, financing programs and partnerships",
        legal_state="candidate_parent_operating_role",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.ENTREPRENEURSHIP, OutreachKind.PARTNERSHIP}),
    ),
    CompanyUnit.OAK: CompanyProfile(
        unit=CompanyUnit.OAK,
        display_name="Tristan OAK Systems",
        role="audit, governance, evidence and risk",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.GOVERNANCE, OutreachKind.SUPPORT}),
    ),
    CompanyUnit.SOFTWARE: CompanyProfile(
        unit=CompanyUnit.SOFTWARE,
        display_name="Tristan Software Labs",
        role="software pilots, integrations and customer discovery",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.SOFTWARE_PILOT, OutreachKind.SUPPORT}),
    ),
    CompanyUnit.RESEARCH: CompanyProfile(
        unit=CompanyUnit.RESEARCH,
        display_name="Tristan Research Foundry",
        role="research pilots, universities and scientific partnerships",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.RESEARCH_PILOT, OutreachKind.PARTNERSHIP}),
    ),
}


FORBIDDEN_PURPOSE_TERMS = frozenset(
    {
        "accept contract",
        "binding acceptance",
        "change banking",
        "wire transfer",
        "admit liability",
        "legal settlement",
        "sign on behalf",
        "government attestation",
    }
)


def validate_policy(case: OutreachCase) -> list[str]:
    errors = case.validate()
    profile = PROFILES[case.company_unit]
    if case.kind not in profile.allowed_kinds:
        errors.append(f"{case.kind.value} is not allowed for {case.company_unit.value}")
    normalized = case.purpose.casefold()
    for term in FORBIDDEN_PURPOSE_TERMS:
        if term in normalized:
            errors.append(f"forbidden purpose term: {term}")
    if case.status is OutreachStatus.SENT and case.source_issue is None:
        errors.append("sent outreach must reference a GitHub issue")
    if case.legal_entity_claimed and profile.legal_state != "incorporated_verified":
        errors.append("company profile is not a verified incorporated legal entity")
    return errors


def disclosure_line(unit: CompanyUnit) -> str:
    profile = PROFILES[unit]
    if profile.legal_state == "incorporated_verified" and profile.verified_domain:
        return profile.display_name
    return f"{profile.display_name} — rôle opérationnel interne/candidat, non présenté comme entité constituée"


def follow_up_allowed(
    case: OutreachCase,
    prior_sent_at: datetime,
    *,
    now: datetime | None = None,
    cooldown_days: int = 14,
    new_event: bool = False,
) -> bool:
    if case.status in {OutreachStatus.CLOSED, OutreachStatus.BLOCKED}:
        return False
    if new_event:
        return True
    current = now or datetime.now(timezone.utc)
    if prior_sent_at.tzinfo is None:
        prior_sent_at = prior_sent_at.replace(tzinfo=timezone.utc)
    return current >= prior_sent_at + timedelta(days=cooldown_days)


def route_kind(kind: OutreachKind) -> CompanyUnit:
    routes = {
        OutreachKind.ENTREPRENEURSHIP: CompanyUnit.PARENT,
        OutreachKind.PARTNERSHIP: CompanyUnit.PARENT,
        OutreachKind.SOFTWARE_PILOT: CompanyUnit.SOFTWARE,
        OutreachKind.RESEARCH_PILOT: CompanyUnit.RESEARCH,
        OutreachKind.GOVERNANCE: CompanyUnit.OAK,
        OutreachKind.SUPPORT: CompanyUnit.OAK,
    }
    return routes[kind]


def audit_cases(cases: Iterable[OutreachCase]) -> list[str]:
    seen_case_ids: set[str] = set()
    seen_receipts: set[str] = set()
    errors: list[str] = []
    for case in cases:
        if case.case_id in seen_case_ids:
            errors.append(f"duplicate case_id: {case.case_id}")
        seen_case_ids.add(case.case_id)
        if case.provider_receipt_hash:
            if case.provider_receipt_hash in seen_receipts:
                errors.append(f"duplicate provider receipt: {case.provider_receipt_hash}")
            seen_receipts.add(case.provider_receipt_hash)
        errors.extend(f"{case.case_id}: {error}" for error in validate_policy(case))
    return errors
