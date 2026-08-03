from __future__ import annotations

from .models import ConsentBasis, NextAction, OutreachCase, RiskTier, StrategicScore, StrategicSignals


def score_case(case: OutreachCase, signals: StrategicSignals) -> StrategicScore:
    errors = signals.validate()
    if errors:
        raise ValueError("; ".join(errors))

    reasons: list[str] = []
    if case.risk_tier is RiskTier.HIGH:
        return StrategicScore(
            case_id=case.case_id,
            score=0,
            disposition="block",
            reasons=("high-risk outreach belongs in Legal Production OS",),
            next_action=NextAction.BLOCK,
        )
    if case.commercial_message and case.consent_basis is ConsentBasis.NONE:
        return StrategicScore(
            case_id=case.case_id,
            score=0,
            disposition="block",
            reasons=("commercial outreach has no consent basis",),
            next_action=NextAction.BLOCK,
        )

    weights = {
        "relevance": 20,
        "decision_authority": 15,
        "problem_fit": 20,
        "evidence_readiness": 15,
        "timing": 10,
        "reciprocity": 10,
        "effort": 5,
        "risk": 5,
    }
    positive = (
        signals.relevance * weights["relevance"]
        + signals.decision_authority * weights["decision_authority"]
        + signals.problem_fit * weights["problem_fit"]
        + signals.evidence_readiness * weights["evidence_readiness"]
        + signals.timing * weights["timing"]
        + signals.reciprocity * weights["reciprocity"]
        + (5 - signals.effort) * weights["effort"]
        + (5 - signals.risk) * weights["risk"]
    )
    score = round(positive / 5)
    if case.risk_tier is RiskTier.MEDIUM:
        score = max(0, score - 15)
        reasons.append("medium-risk case requires human review")
    if not case.corporate_domain_verified:
        reasons.append("personal verified Gmail remains the transport")
    if case.commercial_message:
        reasons.append("commercial-message controls apply")
    else:
        reasons.append("bounded non-commercial or relationship-based outreach")

    if score >= 75 and case.risk_tier is RiskTier.LOW:
        disposition = "send_or_continue"
        action = NextAction.FOLLOW_UP if case.sent_at else NextAction.HUMAN_REVIEW
    elif score >= 55:
        disposition = "draft_for_review"
        action = NextAction.HUMAN_REVIEW
    elif score >= 35:
        disposition = "wait"
        action = NextAction.WAIT
    else:
        disposition = "hold"
        action = NextAction.CLOSE

    return StrategicScore(
        case_id=case.case_id,
        score=score,
        disposition=disposition,
        reasons=tuple(reasons),
        next_action=action,
    )
