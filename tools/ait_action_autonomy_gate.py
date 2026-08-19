"""AIT action autonomy gate for SAFE-GO-MAX.

This module maps a proposed action to a conservative autonomy level. It is a
safety router, not a policy oracle, not legal advice, not medical advice, and
not a substitute for qualified human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Iterable


class AutonomyLevel(IntEnum):
    """SAFE-GO-MAX autonomy scale."""

    L0_EXPLANATION_ONLY = 0
    L1_DRAFT_OR_SIMULATION = 1
    L2_LOCAL_ARTIFACT = 2
    L3_GITHUB_BRANCH = 3
    L4_DRAFT_PR = 4
    L5_PR_READY_FOR_REVIEW = 5
    L6_MERGE_WITH_EXPLICIT_VALIDATION = 6
    L7_MONITORED_DEPLOYMENT = 7
    L8_REVERSIBLE_AUTOMATION = 8
    L9_LOW_RISK_AUTONOMY = 9
    L10_FORBIDDEN = 10


class RiskDomain(StrEnum):
    MEDICAL = "medical"
    EMERGENCY = "emergency"
    BIOLOGICAL = "biological"
    LEGAL = "legal"
    FINANCIAL = "financial"
    PRIVACY = "privacy"
    IP = "intellectual_property"
    CYBERSECURITY = "cybersecurity"
    REPUTATION = "reputation"
    DESTRUCTIVE = "destructive"
    PUBLICATION = "publication"
    LOW_RISK_CREATIVE = "low_risk_creative"
    CODE = "code"
    GITHUB = "github"


class TouchMode(StrEnum):
    ZERO_TOUCH = "ZERO-TOUCH"
    DRY_RUN = "DRY-RUN"
    ONE_TOUCH = "ONE-TOUCH"
    NO_TOUCH = "NO-TOUCH"


@dataclass(frozen=True)
class AutonomyDecision:
    level: AutonomyLevel
    mode: TouchMode
    reason: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]


FORBIDDEN_DOMAINS = {
    RiskDomain.MEDICAL,
    RiskDomain.EMERGENCY,
    RiskDomain.BIOLOGICAL,
    RiskDomain.DESTRUCTIVE,
}

SENSITIVE_DOMAINS = {
    RiskDomain.LEGAL,
    RiskDomain.FINANCIAL,
    RiskDomain.PRIVACY,
    RiskDomain.IP,
    RiskDomain.CYBERSECURITY,
    RiskDomain.REPUTATION,
    RiskDomain.PUBLICATION,
}

SAFE_CREATIVE_DOMAINS = {
    RiskDomain.LOW_RISK_CREATIVE,
    RiskDomain.CODE,
    RiskDomain.GITHUB,
}


def decide_action_autonomy(
    domains: Iterable[RiskDomain | str],
    *,
    irreversible: bool = False,
    public_side_effect: bool = False,
    explicit_user_validation: bool = False,
) -> AutonomyDecision:
    """Choose a conservative autonomy mode for an AIT action.

    Rules
    -----
    - Medical/emergency/biological/destructive or irreversible contexts are
      NO-TOUCH unless the only action is explanation/escalation.
    - Sensitive public or external side-effect contexts are ONE-TOUCH.
    - Sensitive but non-executing contexts are DRY-RUN.
    - Low-risk creative/code/GitHub work may proceed to branch or draft PR.
    """

    normalized = {RiskDomain(d) for d in domains}

    if irreversible or normalized & FORBIDDEN_DOMAINS:
        return AutonomyDecision(
            level=AutonomyLevel.L10_FORBIDDEN,
            mode=TouchMode.NO_TOUCH,
            reason="Medical/emergency/biological/destructive or irreversible risk requires blocking autonomous action.",
            allowed_actions=(
                "explain safely",
                "prepare a reversible draft",
                "route to qualified human help",
                "document generic OAK-safe safeguards",
            ),
            forbidden_actions=(
                "autonomous medical triage",
                "dose calculation",
                "irreversible execution",
                "deletion",
                "public leak of sensitive data",
                "deployment without explicit validation",
            ),
        )

    if normalized & SENSITIVE_DOMAINS:
        if public_side_effect or explicit_user_validation:
            return AutonomyDecision(
                level=AutonomyLevel.L6_MERGE_WITH_EXPLICIT_VALIDATION,
                mode=TouchMode.ONE_TOUCH,
                reason="Sensitive external or public side-effect requires explicit validation before execution.",
                allowed_actions=("draft", "simulate", "prepare PR", "request explicit validation"),
                forbidden_actions=("auto-merge", "auto-send", "auto-publish", "auto-contract", "auto-payment"),
            )
        return AutonomyDecision(
            level=AutonomyLevel.L1_DRAFT_OR_SIMULATION,
            mode=TouchMode.DRY_RUN,
            reason="Sensitive domain without execution should stay in dry-run/simulation.",
            allowed_actions=("draft", "simulate", "risk-map", "prepare review checklist"),
            forbidden_actions=("external execution", "publication", "financial/legal commitment"),
        )

    if normalized <= SAFE_CREATIVE_DOMAINS and normalized:
        return AutonomyDecision(
            level=AutonomyLevel.L4_DRAFT_PR,
            mode=TouchMode.ZERO_TOUCH,
            reason="Low-risk creative/code/GitHub task may proceed to branch and draft PR.",
            allowed_actions=("create branch", "create file", "open draft PR", "add tests", "add OAK notes"),
            forbidden_actions=("auto-merge without explicit validation",),
        )

    return AutonomyDecision(
        level=AutonomyLevel.L0_EXPLANATION_ONLY,
        mode=TouchMode.DRY_RUN,
        reason="Unknown or mixed risk defaults to explanation/dry-run.",
        allowed_actions=("explain", "ask for qualified review if needed", "prepare non-executing draft"),
        forbidden_actions=("autonomous execution",),
    )
