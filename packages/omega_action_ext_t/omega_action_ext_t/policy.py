"""Compact OAK-safe decision gate for external actions."""

from __future__ import annotations

from .core import ActionDNA, AutonomyLevel, Decision, DryRunReport
from .leak_scan import has_findings


class OAKGate:
    """Conservative pre-execution filter.

    The gate prefers draft/dry-run/review over direct execution when an action
    touches people, public outputs, money, IP, high risk, or weak reversibility.
    """

    def __init__(self, auto_total_threshold: int = 3) -> None:
        self.auto_total_threshold = auto_total_threshold

    def evaluate(self, action: ActionDNA) -> tuple[Decision, AutonomyLevel, list[str], list[str], list[str]]:
        reasons: list[str] = []
        approvals: list[str] = []
        blockers: list[str] = []

        payload_text = str(action.metadata.get("payload_text", "")) if action.metadata else ""
        if action.public and payload_text and has_findings(payload_text):
            blockers.append("public_payload_leak_finding")
            reasons.append("Public payload has obvious sensitive markers and must be blocked.")
            return Decision.BLOCK, AutonomyLevel.L5_BLOCKED, reasons, approvals, blockers

        if action.destructive and not action.rollback:
            blockers.append("missing_rollback")
            reasons.append("Action changes important state without a rollback plan.")
            return Decision.BLOCK, AutonomyLevel.L5_BLOCKED, reasons, approvals, blockers

        if action.touches_health or action.touches_safety or action.risk.safety >= 4:
            approvals.append("qualified_review")
            reasons.append("Sensitive physical or health-related action requires qualified review.")
            return Decision.REQUIRE_EXPERT, AutonomyLevel.L4_CO_SIGNED, reasons, approvals, blockers

        if action.risk.max_axis >= 5:
            approvals.append("expert_review")
            reasons.append("At least one risk axis is critical.")
            return Decision.REQUIRE_EXPERT, AutonomyLevel.L4_CO_SIGNED, reasons, approvals, blockers

        if action.touches_money and not action.approved:
            approvals.append("explicit_financial_approval")
            reasons.append("Financial action requires explicit approval.")
            return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

        if action.public and action.touches_ip and not action.approved:
            approvals.append("ip_review")
            reasons.append("Public IP-relevant action requires review.")
            return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

        if action.action_type.lower() == "send_email" and not action.approved:
            approvals.append("explicit_send_confirmation")
            reasons.append("Email sending without approval is downgraded to draft-only.")
            return Decision.ALLOW_DRAFT, AutonomyLevel.L1_DRAFT_ONLY, reasons, approvals, blockers

        if action.touches_humans and not action.approved and action.risk.reputation >= 2:
            approvals.append("human_context_review")
            reasons.append("Human-facing action with reputation risk requires review.")
            return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

        if action.risk.total >= 10 and not action.approved:
            approvals.append("high_risk_approval")
            reasons.append("High aggregate risk requires approval.")
            return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

        if action.reversible and action.risk.total <= self.auto_total_threshold:
            reasons.append("Low-risk reversible action may run with logging.")
            return Decision.ALLOW_AUTO, AutonomyLevel.L2_REVERSIBLE_SAFE, reasons, approvals, blockers

        if action.approved:
            reasons.append("Approved action still needs proof logging.")
            return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

        approvals.append("tristan_review")
        reasons.append("Default conservative route: dry-run and review.")
        return Decision.NEEDS_APPROVAL, AutonomyLevel.L3_APPROVED_EXECUTION, reasons, approvals, blockers

    def dry_run(self, action: ActionDNA) -> DryRunReport:
        decision, level, reasons, approvals, blockers = self.evaluate(action)
        return DryRunReport(
            action=action,
            decision=decision,
            autonomy_level=level,
            reasons=reasons,
            required_approvals=approvals,
            expected_effects=self._expected_effects(decision),
            rollback_plan=action.rollback if action.rollback else None,
            blocked_by=blockers,
        )

    @staticmethod
    def _expected_effects(decision: Decision) -> list[str]:
        if decision == Decision.BLOCK:
            return ["No external effect; action is blocked."]
        if decision == Decision.ALLOW_DRAFT:
            return ["Prepare draft only; do not perform final external action."]
        if decision == Decision.ALLOW_AUTO:
            return ["Run within reversible low-risk scope and write proof log."]
        if decision == Decision.REQUIRE_EXPERT:
            return ["Prepare a review packet; no autonomous execution."]
        return ["Prepare dry-run packet and wait for approval before execution."]
