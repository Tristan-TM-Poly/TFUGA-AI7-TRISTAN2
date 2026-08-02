"""Risk-proportional reply and delivery policy gate."""
from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    AutonomousDeliveryContract,
    CaseRecord,
    Channel,
    DataClass,
    GateResult,
    Intent,
    ReplyDecision,
)

CLASS_RANK = {
    DataClass.PUBLIC: 0,
    DataClass.INTERNAL: 1,
    DataClass.CLIENT_CONFIDENTIAL: 2,
    DataClass.PERSONAL: 3,
    DataClass.RESTRICTED: 4,
    DataClass.SECRET: 5,
}

PROFESSIONAL_INTENTS = {
    Intent.CONTRACT_OR_LEGAL,
    Intent.GOVERNMENT_OR_TAX,
}
CRITICAL_INTENTS = {
    Intent.SECURITY_INCIDENT,
    Intent.PAYMENT_CHANGE,
}
APPROVAL_INTENTS = {
    Intent.IP_OR_CONFIDENTIAL,
    Intent.PRIVACY_REQUEST,
    Intent.PROPOSAL_REQUEST,
    Intent.QUOTE_REQUEST,
    Intent.INVOICE_REQUEST,
}
AUTO_DRAFT_INTENTS = {
    Intent.TECHNICAL_REPORT,
    Intent.BUG_REPORT,
    Intent.FEATURE_REQUEST,
    Intent.DOCUMENT_REQUEST,
}
AUTO_REPLY_INTENTS = {
    Intent.ACKNOWLEDGMENT,
    Intent.STATUS_REQUEST,
    Intent.SUPPORT_QUESTION,
}


def _expired(value: str | None) -> bool:
    if not value:
        return False
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed < datetime.now(timezone.utc)


def gate_case(case: CaseRecord, contract: AutonomousDeliveryContract) -> GateResult:
    reasons: list[str] = []
    analysis = case.analysis
    identity = case.identity

    if contract.kill_switch:
        return GateResult(case.case_id, ReplyDecision.BLOCK, ("delivery_contract_kill_switch",))
    if _expired(contract.expires_at):
        return GateResult(case.case_id, ReplyDecision.BLOCK, ("delivery_contract_expired",))
    if analysis.primary_intent not in contract.allowed_intents:
        reasons.append("intent_not_pre_authorized")
    if identity.identity_confidence < contract.minimum_identity_confidence:
        reasons.append("identity_confidence_below_policy")
    if identity.authority_confidence < contract.minimum_authority_confidence:
        reasons.append("authority_confidence_below_policy")
    if CLASS_RANK[analysis.requested_data_class] > CLASS_RANK[contract.maximum_data_class]:
        reasons.append("requested_data_class_exceeds_policy")

    if analysis.primary_intent in CRITICAL_INTENTS:
        decision = ReplyDecision.REQUIRE_TWO_APPROVALS
        reasons.append("critical_intent")
    elif analysis.primary_intent in PROFESSIONAL_INTENTS:
        decision = ReplyDecision.PROFESSIONAL_REVIEW
        reasons.append("legal_tax_or_government_domain")
    elif analysis.primary_intent in APPROVAL_INTENTS:
        decision = ReplyDecision.REQUIRE_APPROVAL
        reasons.append("sensitive_or_commercial_commitment")
    elif analysis.primary_intent is Intent.UNKNOWN or analysis.ambiguities:
        decision = ReplyDecision.REQUIRE_INFORMATION
        reasons.append("unresolved_request")
    elif reasons:
        decision = ReplyDecision.REQUIRE_APPROVAL
    elif analysis.primary_intent in AUTO_DRAFT_INTENTS:
        decision = ReplyDecision.AUTO_PRODUCE_DRAFT_DISPATCH
    elif analysis.primary_intent in AUTO_REPLY_INTENTS:
        decision = ReplyDecision.AUTO_REPLY
    else:
        decision = ReplyDecision.REQUIRE_APPROVAL

    if analysis.requested_data_class in {DataClass.PERSONAL, DataClass.RESTRICTED, DataClass.SECRET}:
        if decision in {ReplyDecision.AUTO_REPLY, ReplyDecision.AUTO_PRODUCE_DRAFT_DISPATCH, ReplyDecision.AUTO_BOUNDED_DISPATCH}:
            decision = ReplyDecision.REQUIRE_APPROVAL
        reasons.append("sensitive_data_class")

    approvals = 2 if decision is ReplyDecision.REQUIRE_TWO_APPROVALS else 1 if decision is ReplyDecision.REQUIRE_APPROVAL else 0
    return GateResult(
        case_id=case.case_id,
        decision=decision,
        reasons=tuple(dict.fromkeys(reasons)) or ("bounded_policy_match",),
        required_approvals=approvals,
        allowed_channels=tuple(contract.allowed_channels),
        allowed_deliverables=tuple(contract.allowed_deliverables),
    )
