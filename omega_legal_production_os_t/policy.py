"""Default-deny OAK policy gate for external corporate actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .models import (
    ActionType,
    AuthorityGrant,
    ExternalActionEnvelope,
    GateDecision,
    RiskLevel,
)


_PERMISSION_BY_TYPE: dict[ActionType, str] = {
    ActionType.EXTERNAL_MAIL: "execute_external_mail",
    ActionType.RELEASE: "publish_release",
    ActionType.PAYMENT: "execute_payment",
    ActionType.SIGNATURE: "dispatch_signature",
    ActionType.GOVERNMENT_FILING: "submit_government_filing",
    ActionType.INCORPORATION: "submit_incorporation",
    ActionType.PRODUCTION_ACTIVATION: "activate_production",
}

_PROFESSIONAL_TYPES = frozenset(
    {
        ActionType.SIGNATURE,
        ActionType.GOVERNMENT_FILING,
        ActionType.INCORPORATION,
    }
)


@dataclass(frozen=True, slots=True)
class PolicyReport:
    decision: GateDecision
    reasons: tuple[str, ...]
    checks: Mapping[str, bool]
    action_hash: str
    permission: str

    @property
    def allowed(self) -> bool:
        return self.decision in {GateDecision.ALLOW_DRY_RUN, GateDecision.ALLOW_EXECUTION}

    def to_mapping(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
            "action_hash": self.action_hash,
            "permission": self.permission,
        }


class LegalProductionPolicyGate:
    """Evaluate one immutable action envelope against bounded authority."""

    def evaluate(
        self,
        action: ExternalActionEnvelope,
        *,
        grants: Sequence[AuthorityGrant] = (),
        execute: bool = False,
    ) -> PolicyReport:
        reasons: list[str] = []
        checks: dict[str, bool] = {}
        permission = _PERMISSION_BY_TYPE[action.action_type]

        def check(name: str, passed: bool, reason: str) -> None:
            checks[name] = bool(passed)
            if not passed:
                reasons.append(reason)

        check("action_valid", not action.validate(), "action_validation_failed")
        check("policy_selected", action.policy_id != "DEFAULT-DENY", "explicit_policy_required")
        check("company_present", bool(action.company_id.strip()), "company_missing")
        check("purpose_present", bool(action.purpose.strip()), "purpose_missing")
        check("payload_present", bool(action.payload), "payload_missing")

        self._check_type_specific(action, check)

        professional_evidence = any(
            evidence.startswith("professional-review:") for evidence in action.evidence_ids
        )
        if action.action_type in _PROFESSIONAL_TYPES or action.professional_review_required:
            check(
                "professional_review",
                professional_evidence,
                "professional_review_evidence_missing",
            )
        else:
            checks["professional_review"] = True

        if not execute:
            if reasons:
                decision = (
                    GateDecision.PROFESSIONAL_REVIEW
                    if reasons == ["professional_review_evidence_missing"]
                    else GateDecision.BLOCK
                )
            else:
                decision = GateDecision.ALLOW_DRY_RUN
            return PolicyReport(decision, tuple(reasons), checks, action.action_hash, permission)

        amount = _amount(action.payload)
        jurisdiction = str(action.payload.get("jurisdiction", "")).strip() or None
        authorized_people = {
            approval.approver.casefold()
            for approval in action.approvals
            if any(
                grant.person_id.casefold() == approval.approver.casefold()
                and grant.role.casefold() == approval.role.casefold()
                and grant.permits(
                    permission,
                    company_id=action.company_id,
                    amount_cad=amount,
                    jurisdiction=jurisdiction,
                )
                for grant in grants
            )
        }
        check(
            "authority_grants",
            len(authorized_people) >= action.required_approvals,
            "insufficient_authorized_approvers",
        )
        check(
            "approval_count",
            len(action.approvals) >= action.required_approvals,
            "approval_count_insufficient",
        )
        check(
            "approval_hashes",
            all(not approval.validate_for(action) for approval in action.approvals),
            "approval_invalid",
        )

        if reasons:
            if "professional_review_evidence_missing" in reasons:
                decision = GateDecision.PROFESSIONAL_REVIEW
            elif "approval_count_insufficient" in reasons or "insufficient_authorized_approvers" in reasons:
                decision = (
                    GateDecision.REQUIRE_TWO_APPROVALS
                    if action.required_approvals == 2
                    else GateDecision.REQUIRE_APPROVAL
                )
            elif reasons == ["action_validation_failed"]:
                decision = GateDecision.REQUIRE_INFORMATION
            else:
                decision = GateDecision.BLOCK
        else:
            decision = GateDecision.ALLOW_EXECUTION
        return PolicyReport(decision, tuple(reasons), checks, action.action_hash, permission)

    @staticmethod
    def _check_type_specific(action: ExternalActionEnvelope, check) -> None:
        payload = action.payload
        if action.action_type == ActionType.EXTERNAL_MAIL:
            check("recipient_hash", _is_sha256(payload.get("recipient_hash")), "recipient_hash_missing")
            check("message_hash", _is_sha256(payload.get("message_hash")), "message_hash_missing")
            check("single_message", payload.get("message_count") == 1, "exactly_one_message_required")
        elif action.action_type == ActionType.RELEASE:
            check("commit_sha", _is_commit(payload.get("commit_sha")), "release_commit_invalid")
            check("tag", _valid_tag(payload.get("tag"), payload.get("version")), "release_tag_invalid")
            artifacts = payload.get("artifacts", ())
            check("artifacts", bool(artifacts), "release_artifacts_missing")
            check(
                "artifact_hashes",
                bool(artifacts)
                and all(_is_sha256(item.get("sha256")) for item in artifacts if isinstance(item, Mapping)),
                "release_artifact_hash_invalid",
            )
            validations = payload.get("validations", {})
            check(
                "release_validations",
                all(validations.get(name) == "PASS" for name in ("tests", "licenses", "sbom", "install")),
                "release_validation_incomplete",
            )
        elif action.action_type == ActionType.PAYMENT:
            amount = _amount(payload)
            check("payment_amount", amount is not None and amount > 0, "payment_amount_invalid")
            check("currency", payload.get("currency") == "CAD", "payment_currency_not_allowed")
            check("invoice_hash", _is_sha256(payload.get("invoice_hash")), "invoice_hash_missing")
            check("counterparty_verified", payload.get("counterparty_verified") is True, "counterparty_unverified")
            check("no_crypto", payload.get("rail") != "CRYPTO", "crypto_payment_blocked")
        elif action.action_type == ActionType.SIGNATURE:
            check("document_hash", _is_sha256(payload.get("document_hash")), "document_hash_missing")
            check("signer_role", bool(str(payload.get("signer_role", "")).strip()), "signer_role_missing")
            check("authority_evidence", _is_sha256(payload.get("authority_evidence_hash")), "signature_authority_missing")
        elif action.action_type == ActionType.GOVERNMENT_FILING:
            check("jurisdiction", bool(str(payload.get("jurisdiction", "")).strip()), "jurisdiction_missing")
            check("filing_hash", _is_sha256(payload.get("filing_hash")), "filing_hash_missing")
            check("attestation", payload.get("human_attestation_required") is True, "human_attestation_required")
        elif action.action_type == ActionType.INCORPORATION:
            check("jurisdiction", payload.get("jurisdiction") in {"QC", "CA"}, "incorporation_jurisdiction_invalid")
            check("founding_packet", _is_sha256(payload.get("founding_packet_hash")), "founding_packet_hash_missing")
            check("founder_approval", payload.get("founder_approval_required") is True, "founder_approval_required")
        elif action.action_type == ActionType.PRODUCTION_ACTIVATION:
            check("release_hash", _is_sha256(payload.get("release_hash")), "production_release_hash_missing")
            check("readiness_hash", _is_sha256(payload.get("readiness_hash")), "readiness_hash_missing")
            check("rollback_hash", _is_sha256(payload.get("rollback_plan_hash")), "rollback_plan_hash_missing")
            check("canary", payload.get("canary_required") is True, "production_canary_required")


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        return False
    try:
        int(value[7:], 16)
    except ValueError:
        return False
    return True


def _is_commit(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _valid_tag(tag: Any, version: Any) -> bool:
    return isinstance(tag, str) and isinstance(version, str) and tag == f"v{version}" and bool(version)


def _amount(payload: Mapping[str, Any]) -> float | None:
    value = payload.get("amount_cad")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
