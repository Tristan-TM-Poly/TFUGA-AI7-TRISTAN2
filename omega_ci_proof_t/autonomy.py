from __future__ import annotations

from .models import AutonomyDecision

_LEVELS = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7")


class AutonomyGate:
    """R0.1 grants at most A3 and never grants merge authority."""

    MAX_IMPLEMENTED_LEVEL = "A3"

    def evaluate(
        self,
        requested_level: str,
        *,
        risk: str = "low",
        reversible: bool = True,
        public_api_change: bool = False,
        security_sensitive: bool = False,
        ip_sensitive: bool = False,
        financial_effect: bool = False,
    ) -> AutonomyDecision:
        if requested_level not in _LEVELS:
            raise ValueError(f"unknown autonomy level: {requested_level}")
        reasons: list[str] = []
        allowed = _LEVELS.index(requested_level) <= _LEVELS.index(self.MAX_IMPLEMENTED_LEVEL)
        if not allowed:
            reasons.append("R0.1 implements evidence planning and test generation only; A4-A7 remain disabled")
        if risk != "low":
            allowed = False
            reasons.append("only low-risk work may proceed without a new human decision")
        if not reversible:
            allowed = False
            reasons.append("irreversible actions require Tristan")
        if public_api_change or security_sensitive or ip_sensitive or financial_effect:
            allowed = False
            reasons.append("public API, security, IP, or financial effects require Tristan")
        granted = requested_level if allowed else self.MAX_IMPLEMENTED_LEVEL if requested_level in {"A4", "A5", "A6", "A7"} else "A0"
        return AutonomyDecision(
            requested_level=requested_level,
            granted_level=granted,
            allowed=allowed,
            automatic_merge_allowed=False,
            human_review_required=True,
            reasons=tuple(reasons or ["A1-A3 operation is permitted, but promotion and merge remain human-reviewed"]),
        )
