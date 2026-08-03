from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .models import (
    CompanyUnit,
    ConsentBasis,
    MailEventType,
    NextAction,
    OutreachCase,
    OutreachKind,
    OutreachStatus,
    PublicMailEvent,
    ReplyClass,
    RiskTier,
)


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    unit: CompanyUnit
    display_name: str
    role: str
    legal_state: str
    verified_domain: bool
    allowed_kinds: frozenset[OutreachKind]
    voice_traits: tuple[str, ...]
    maximum_daily_sends: int = 5


@dataclass(frozen=True, slots=True)
class OutreachBudget:
    maximum_daily_sends: int = 5
    maximum_sends_per_organization_30d: int = 2
    maximum_unanswered_followups: int = 1
    maximum_open_cases: int = 12


PROFILES = {
    CompanyUnit.PARENT: CompanyProfile(
        unit=CompanyUnit.PARENT,
        display_name="Tristan Parent OpCo",
        role="strategy, entrepreneurship, financing programs and partnerships",
        legal_state="candidate_parent_operating_role",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.ENTREPRENEURSHIP, OutreachKind.PARTNERSHIP}),
        voice_traits=("concise", "commercially grounded", "evidence-aware", "non-binding"),
    ),
    CompanyUnit.OAK: CompanyProfile(
        unit=CompanyUnit.OAK,
        display_name="Tristan OAK Systems",
        role="audit, governance, evidence and risk",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.GOVERNANCE, OutreachKind.SUPPORT}),
        voice_traits=("precise", "traceable", "risk-explicit", "non-adversarial"),
    ),
    CompanyUnit.SOFTWARE: CompanyProfile(
        unit=CompanyUnit.SOFTWARE,
        display_name="Tristan Software Labs",
        role="software pilots, integrations and customer discovery",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.SOFTWARE_PILOT, OutreachKind.SUPPORT}),
        voice_traits=("technical", "prototype-first", "measurable", "low-friction"),
    ),
    CompanyUnit.RESEARCH: CompanyProfile(
        unit=CompanyUnit.RESEARCH,
        display_name="Tristan Research Foundry",
        role="research pilots, universities and scientific partnerships",
        legal_state="internal_division",
        verified_domain=False,
        allowed_kinds=frozenset({OutreachKind.RESEARCH_PILOT, OutreachKind.PARTNERSHIP}),
        voice_traits=("scholarly", "bounded", "falsifiable", "institutionally respectful"),
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
        "guaranteed return",
        "guaranteed revenue",
        "confidential credentials",
        "password",
        "private key",
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
    if case.status not in {OutreachStatus.PREPARED, OutreachStatus.APPROVED} and case.source_issue is None:
        errors.append("external outreach must reference a GitHub issue")
    if case.legal_entity_claimed and profile.legal_state != "incorporated_verified":
        errors.append("company profile is not a verified incorporated legal entity")
    if case.corporate_domain_verified and not profile.verified_domain:
        errors.append("case cannot override an unverified company-domain registry")
    if case.risk_tier is RiskTier.HIGH:
        errors.append("high-risk outreach requires a separate legal-production action")
    if case.commercial_message and case.consent_basis in {
        ConsentBasis.PUBLIC_INSTITUTIONAL_CONTACT,
        ConsentBasis.NOT_COMMERCIAL,
        ConsentBasis.NONE,
    }:
        errors.append("commercial message consent basis is insufficient")
    return errors


def disclosure_line(unit: CompanyUnit) -> str:
    profile = PROFILES[unit]
    if profile.legal_state == "incorporated_verified" and profile.verified_domain:
        return profile.display_name
    return (
        f"{profile.display_name} — rôle opérationnel interne/candidat, "
        "non présenté comme entité constituée"
    )


def company_signature(unit: CompanyUnit, sender_name: str = "Tristan Tardif-Morency") -> str:
    profile = PROFILES[unit]
    return f"{sender_name}\npour {profile.display_name}\n{disclosure_line(unit)}"


def follow_up_allowed(
    case: OutreachCase,
    prior_sent_at: datetime,
    *,
    now: datetime | None = None,
    cooldown_days: int = 14,
    new_event: bool = False,
    unanswered_followups: int = 0,
) -> bool:
    if case.status in {OutreachStatus.CLOSED, OutreachStatus.BLOCKED}:
        return False
    if case.reply_class in {ReplyClass.DECLINE, ReplyClass.UNSUBSCRIBE, ReplyClass.BOUNCE}:
        return False
    if unanswered_followups >= 1 and not new_event:
        return False
    if new_event:
        return True
    current = now or datetime.now(timezone.utc)
    if prior_sent_at.tzinfo is None:
        prior_sent_at = prior_sent_at.replace(tzinfo=timezone.utc)
    return current >= prior_sent_at + timedelta(days=cooldown_days)


def route_kind(kind: OutreachKind, *, research_context: bool = False) -> CompanyUnit:
    if kind is OutreachKind.PARTNERSHIP and research_context:
        return CompanyUnit.RESEARCH
    routes = {
        OutreachKind.ENTREPRENEURSHIP: CompanyUnit.PARENT,
        OutreachKind.PARTNERSHIP: CompanyUnit.PARENT,
        OutreachKind.SOFTWARE_PILOT: CompanyUnit.SOFTWARE,
        OutreachKind.RESEARCH_PILOT: CompanyUnit.RESEARCH,
        OutreachKind.GOVERNANCE: CompanyUnit.OAK,
        OutreachKind.SUPPORT: CompanyUnit.OAK,
    }
    return routes[kind]


def next_action_for_event(event: PublicMailEvent) -> NextAction:
    if event.event_type is MailEventType.AUTO_REPLY or event.reply_class is ReplyClass.AUTO_REPLY:
        return NextAction.WAIT
    if event.event_type is MailEventType.BOUNCE or event.reply_class is ReplyClass.BOUNCE:
        return NextAction.CORRECT_ADDRESS
    if event.event_type is MailEventType.UNSUBSCRIBE or event.reply_class is ReplyClass.UNSUBSCRIBE:
        return NextAction.CLOSE
    if event.reply_class is ReplyClass.POSITIVE:
        return NextAction.PREPARE_MEETING
    if event.reply_class is ReplyClass.INFORMATION_REQUEST:
        return NextAction.PREPARE_EVIDENCE
    if event.reply_class is ReplyClass.REFERRAL:
        return NextAction.REVIEW_REFERRAL
    if event.reply_class is ReplyClass.DECLINE:
        return NextAction.CLOSE
    return NextAction.HUMAN_REVIEW


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


def validate_portfolio(
    cases: Iterable[OutreachCase],
    *,
    now: datetime | None = None,
    budget: OutreachBudget = OutreachBudget(),
) -> list[str]:
    current = now or datetime.now(timezone.utc)
    cases_list = list(cases)
    errors: list[str] = []
    open_cases = [
        case for case in cases_list
        if case.status not in {OutreachStatus.CLOSED, OutreachStatus.BLOCKED}
    ]
    if len(open_cases) > budget.maximum_open_cases:
        errors.append("maximum open outreach cases exceeded")

    sent_today = 0
    per_org_30d: dict[str, int] = {}
    for case in cases_list:
        if not case.sent_at:
            continue
        try:
            sent = datetime.fromisoformat(case.sent_at)
        except ValueError:
            try:
                sent = datetime.fromisoformat(case.sent_at + "T00:00:00")
            except ValueError:
                errors.append(f"{case.case_id}: invalid sent_at")
                continue
        if sent.tzinfo is None:
            sent = sent.replace(tzinfo=timezone.utc)
        if sent.date() == current.date():
            sent_today += 1
        if current - sent <= timedelta(days=30):
            key = case.target_organization.casefold().strip()
            per_org_30d[key] = per_org_30d.get(key, 0) + 1

    if sent_today > budget.maximum_daily_sends:
        errors.append("maximum daily external sends exceeded")
    for organization, count in per_org_30d.items():
        if count > budget.maximum_sends_per_organization_30d:
            errors.append(f"30-day organization quota exceeded: {organization}")
    return errors
