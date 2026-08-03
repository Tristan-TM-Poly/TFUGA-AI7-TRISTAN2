from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import CapabilityToken, ConstitutionAudit, stable_digest
from .expiry import parse_time

_LEVELS = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")
_SENSITIVE = {"push_patch", "merge", "release", "modify_security_policy", "read_secrets", "financial_action", "public_action", "ip_action"}
_REQUIRED_PRINCIPLES = {
    "no_scientific_claim_without_evidence_class",
    "no_sensitive_merge_without_human_approval",
    "no_secret_exfiltration",
    "no_irreversible_action_without_rollback_or_consent",
    "all_autonomous_actions_are_audited",
    "no_self_authority_escalation",
}


class AutonomyConstitution:
    def __init__(self, mapping: Mapping[str, Any]) -> None:
        self.mapping = dict(mapping)

    def audit(self) -> ConstitutionAudit:
        principles = tuple(str(value) for value in self.mapping.get("immutable_principles", ()))
        maximum = str(self.mapping.get("maximum_authorized_level", "A0"))
        permissions = self.mapping.get("permissions", {})
        errors: list[str] = []
        warnings: list[str] = []
        missing = sorted(_REQUIRED_PRINCIPLES.difference(principles))
        if missing:
            errors.append(f"missing immutable principles: {', '.join(missing)}")
        if maximum not in _LEVELS or _LEVELS.index(maximum) > _LEVELS.index("A3"):
            errors.append("R0.2 constitution cannot authorize above A3")
        if not isinstance(permissions, Mapping):
            errors.append("permissions must be a mapping")
        else:
            for level, actions in permissions.items():
                if str(level) in {"A0", "A1", "A2", "A3"}:
                    overlap = _SENSITIVE.intersection(str(value) for value in actions)
                    if overlap:
                        errors.append(f"sensitive actions permitted at {level}: {', '.join(sorted(overlap))}")
        if self.mapping.get("automatic_merge_allowed") is not False:
            errors.append("automatic merge must be explicitly false")
        if not self.mapping.get("human_review_required", False):
            errors.append("human review must be explicitly required")
        if not self.mapping.get("amendment_requires_separate_pr", False):
            warnings.append("constitution amendment should require a separate PR")
        return ConstitutionAudit(
            passed=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
            immutable_principles=tuple(sorted(principles)),
            maximum_authorized_level=maximum,
            constitution_digest=stable_digest(self.mapping),
        )

    def issue_token(
        self,
        *,
        agent: str,
        run_id: str,
        level: str,
        requested_actions: Sequence[str],
        scope: Sequence[str],
        issued_at: str,
        expires_at: str,
    ) -> CapabilityToken:
        audit = self.audit()
        if not audit.passed:
            raise ValueError("constitution audit failed")
        if level not in _LEVELS or _LEVELS.index(level) > _LEVELS.index(audit.maximum_authorized_level):
            raise PermissionError("requested level exceeds constitution")
        permissions = self.mapping.get("permissions", {})
        allowed_at_level: set[str] = set()
        for candidate in _LEVELS[: _LEVELS.index(level) + 1]:
            allowed_at_level.update(str(value) for value in permissions.get(candidate, ()))
        requested = set(str(value) for value in requested_actions)
        if requested.intersection(_SENSITIVE):
            raise PermissionError("sensitive capabilities require Tristan")
        if not requested.issubset(allowed_at_level):
            raise PermissionError("requested capability is not constitutionally allowed")
        if parse_time(expires_at) <= parse_time(issued_at):
            raise ValueError("capability token expiry must follow issuance")
        return CapabilityToken(
            agent=agent,
            run_id=run_id,
            level=level,
            allowed_actions=tuple(sorted(requested)),
            forbidden_actions=tuple(sorted(_SENSITIVE)),
            scope=tuple(sorted(set(str(value) for value in scope))),
            issued_at=issued_at,
            expires_at=expires_at,
        )

    def authorize(self, token: CapabilityToken, *, action: str, resource: str, now: str) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if parse_time(now) > parse_time(token.expires_at):
            reasons.append("capability token expired")
        if action not in token.allowed_actions:
            reasons.append("action not granted")
        if action in token.forbidden_actions or action in _SENSITIVE:
            reasons.append("sensitive action is constitutionally forbidden")
        if token.scope and not any(resource == prefix or resource.startswith(prefix.rstrip("/") + "/") for prefix in token.scope):
            reasons.append("resource outside token scope")
        return (not reasons, tuple(reasons))
