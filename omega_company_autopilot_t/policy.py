"""OAK policy engine for bounded corporate autonomy."""
from __future__ import annotations

from dataclasses import dataclass

from .models import ActionKind, ActionRequest, AutonomyLevel, CompanyRecord, CompanyState, GateDecision, GateResult, RiskLevel, TreasuryPolicy

_ALWAYS_PROFESSIONAL = {
    ActionKind.CONTRACT_ACCEPT,
    ActionKind.GOVERNMENT_FILING_SUBMIT,
    ActionKind.TAX_RETURN_FILE,
    ActionKind.BANK_ACCOUNT_OPEN,
    ActionKind.SHARE_ISSUANCE,
    ActionKind.IP_ASSIGN,
    ActionKind.HIRE_COMMIT,
}
_ALWAYS_HUMAN = {
    ActionKind.PAYMENT_EXECUTE,
    ActionKind.CONTRACT_ACCEPT,
    ActionKind.GOVERNMENT_FILING_SUBMIT,
    ActionKind.TAX_RETURN_FILE,
    ActionKind.BANK_ACCOUNT_OPEN,
    ActionKind.SHARE_ISSUANCE,
    ActionKind.IP_PUBLISH,
    ActionKind.IP_ASSIGN,
    ActionKind.HIRE_COMMIT,
    ActionKind.DNS_CHANGE,
    ActionKind.DATA_DELETE,
    ActionKind.PUBLIC_CLAIM,
}
_PREPARATION_ACTIONS = {
    ActionKind.INTERNAL_REPORT,
    ActionKind.INVOICE_DRAFT,
    ActionKind.PAYMENT_PREPARE,
    ActionKind.CONTRACT_DRAFT,
    ActionKind.GOVERNMENT_FILING_PREPARE,
    ActionKind.TAX_RETURN_PREPARE,
    ActionKind.IP_CLASSIFY,
    ActionKind.HIRE_PREPARE,
}
_PRODUCTION_REQUIRED = {
    ActionKind.EXTERNAL_EMAIL,
    ActionKind.CUSTOMER_SUPPORT,
    ActionKind.INVOICE_SEND,
    ActionKind.PAYMENT_EXECUTE,
    ActionKind.CONTRACT_ACCEPT,
    ActionKind.DOMAIN_RENEW,
    ActionKind.DNS_CHANGE,
    ActionKind.PUBLIC_CLAIM,
}


@dataclass(frozen=True, slots=True)
class CorporatePolicy:
    treasury: TreasuryPolicy = TreasuryPolicy()
    allowed_auto_actions: tuple[ActionKind, ...] = (
        ActionKind.INTERNAL_REPORT,
        ActionKind.INTERNAL_MESSAGE,
        ActionKind.IP_CLASSIFY,
    )


class OAKCorporateGate:
    def __init__(self, policy: CorporatePolicy | None = None) -> None:
        self.policy = policy or CorporatePolicy()

    def evaluate(self, company: CompanyRecord, action: ActionRequest) -> GateResult:
        reasons: list[str] = []
        evidence: list[str] = []
        professionals: list[str] = []
        approvals = 0

        if action.company_id != company.company_id:
            return GateResult(action.action_id, GateDecision.BLOCK, ("company_id_mismatch",))
        if company.state is CompanyState.M_MINUS_HOLD:
            return GateResult(action.action_id, GateDecision.BLOCK, ("company_on_m_minus_hold",))
        if action.division_id:
            try:
                division = company.division(action.division_id)
            except KeyError:
                return GateResult(action.action_id, GateDecision.BLOCK, ("unknown_division",))
            if not division.enabled:
                return GateResult(action.action_id, GateDecision.BLOCK, ("division_disabled",))

        if action.kind in _PRODUCTION_REQUIRED and company.state is not CompanyState.PRODUCTION_AUTHORIZED:
            reasons.append("production_authorization_required")
        if action.external_effect and not company.production_enabled:
            reasons.append("production_disabled")
        if action.kind is ActionKind.EXTERNAL_EMAIL and not company.external_mail_enabled:
            reasons.append("external_mail_disabled")
        if action.kind is ActionKind.INVOICE_SEND and not company.invoice_send_enabled:
            reasons.append("invoice_send_disabled")
        if action.kind is ActionKind.CONTRACT_ACCEPT and not company.contract_acceptance_enabled:
            reasons.append("contract_acceptance_disabled")
        if action.kind is ActionKind.PAYMENT_EXECUTE and not company.banking_enabled:
            reasons.append("banking_disabled")

        if action.kind in _ALWAYS_PROFESSIONAL:
            professionals.append(self._professional_for(action.kind))
            approvals = max(approvals, 1)
        if action.kind in _ALWAYS_HUMAN:
            approvals = max(approvals, 1)
        if not action.reversible:
            approvals = max(approvals, 1)
            evidence.append("rollback_or_irreversibility_acknowledgement")
        if action.risk_level is RiskLevel.CRITICAL:
            approvals = max(approvals, 2)
            evidence.append("critical_risk_assessment")
        elif action.risk_level is RiskLevel.HIGH:
            approvals = max(approvals, 1)
            evidence.append("risk_assessment")

        amount_limit: float | None = None
        if action.amount_cad is not None:
            if action.amount_cad < 0:
                reasons.append("negative_amount")
            amount_limit = self.policy.treasury.single_approval_limit_cad
            if action.amount_cad >= self.policy.treasury.two_approval_threshold_cad:
                approvals = max(approvals, 2)
            elif action.amount_cad > 0:
                approvals = max(approvals, 1)
            if action.payload.get("category") in self.policy.treasury.prohibited_categories:
                approvals = max(approvals, 1)
                evidence.append("category_specific_approval")

        if reasons:
            return GateResult(
                action.action_id,
                GateDecision.BLOCK,
                tuple(sorted(set(reasons))),
                required_approvals=approvals,
                professional_review=tuple(sorted(set(professionals))),
                required_evidence=tuple(sorted(set(evidence))),
                max_amount_cad=amount_limit,
            )

        if professionals:
            decision = GateDecision.PROFESSIONAL_REVIEW
        elif approvals >= 2:
            decision = GateDecision.REQUIRE_TWO_APPROVALS
        elif approvals == 1:
            decision = GateDecision.REQUIRE_APPROVAL
        elif (
            company.autonomy_level.value >= AutonomyLevel.L4_BOUNDED.value
            and action.kind in self.policy.allowed_auto_actions
            and action.risk_level in {RiskLevel.LOW, RiskLevel.MODERATE}
            and action.reversible
            and not action.external_effect
        ):
            decision = GateDecision.AUTO
        elif action.kind in _PREPARATION_ACTIONS:
            decision = GateDecision.PREPARE
        else:
            decision = GateDecision.PREPARE

        return GateResult(
            action.action_id,
            decision,
            ("policy_evaluated",),
            required_approvals=approvals,
            professional_review=tuple(sorted(set(professionals))),
            required_evidence=tuple(sorted(set(evidence))),
            max_amount_cad=amount_limit,
        )

    @staticmethod
    def _professional_for(kind: ActionKind) -> str:
        if kind is ActionKind.TAX_RETURN_FILE:
            return "accountant_or_tax_professional"
        if kind in {ActionKind.GOVERNMENT_FILING_SUBMIT, ActionKind.BANK_ACCOUNT_OPEN}:
            return "authorized_human_operator"
        return "lawyer_or_qualified_professional"
