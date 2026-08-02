"""Evidence-based division-to-subsidiary recommendation."""
from __future__ import annotations

from dataclasses import dataclass

from .models import DivisionRecord


@dataclass(frozen=True, slots=True)
class SpinoutAssessment:
    division_id: str
    score: float
    recommendation: str
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]


class SpinoutEngine:
    def assess(self, division: DivisionRecord) -> SpinoutAssessment:
        revenue_signal = min(1.0, division.recurring_revenue_cad / 250_000.0)
        customer_signal = min(1.0, division.active_customers / 10.0)
        pilot_signal = min(1.0, division.paid_pilots / 3.0)
        partner_signal = min(1.0, division.external_partners / 3.0)
        ip_signal = min(1.0, division.ip_assets / 10.0)
        investor_signal = max(0.0, min(1.0, division.investor_interest))
        liability_signal = max(0.0, min(1.0, division.liability_isolation_need))
        regulation_signal = 1.0 if division.regulated_activity else 0.0
        admin_penalty = min(1.0, division.administrative_cost_cad / 100_000.0)
        score = round(max(0.0, min(1.0,
            0.20 * revenue_signal + 0.15 * customer_signal + 0.10 * pilot_signal
            + 0.10 * partner_signal + 0.15 * ip_signal + 0.10 * investor_signal
            + 0.15 * liability_signal + 0.10 * regulation_signal - 0.15 * admin_penalty
        )), 4)
        reasons: list[str] = []
        blockers: list[str] = []
        if division.recurring_revenue_cad > 0: reasons.append("recurring_revenue")
        if division.paid_pilots > 0: reasons.append("paid_pilot")
        if division.ip_assets > 0: reasons.append("separable_ip")
        if division.liability_isolation_need >= 0.6: reasons.append("liability_isolation")
        if division.regulated_activity: reasons.append("regulated_activity")
        if division.active_customers == 0 and division.paid_pilots == 0: blockers.append("no_customer_or_paid_pilot")
        if division.recurring_revenue_cad == 0: blockers.append("no_recurring_revenue")
        if division.administrative_cost_cad > max(division.revenue_cad, 1.0): blockers.append("administrative_cost_exceeds_revenue")
        if blockers:
            recommendation = "KEEP_AS_DIVISION"
        elif score >= 0.72:
            recommendation = "PROFESSIONAL_SPINOUT_REVIEW"
        elif score >= 0.50:
            recommendation = "PREPARE_SEPARATION_PACKET"
        else:
            recommendation = "KEEP_AS_DIVISION"
        return SpinoutAssessment(division.division_id, score, recommendation, tuple(reasons), tuple(blockers))
