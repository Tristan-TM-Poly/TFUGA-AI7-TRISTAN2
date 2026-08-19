"""Canon Immune Response for Tristan CanonOS.

Maps canon risk signals to conservative review-gated responses. This helper only
returns safe planning labels; it does not execute external actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CanonSignal(StrEnum):
    OVERCLAIM = "overclaim"
    IRREVERSIBLE_CHANGE = "irreversible_change"
    SENSITIVE_DATA = "sensitive_data"
    QUALIFIED_REVIEW_DOMAIN = "qualified_review_domain"
    WEAK_EVIDENCE = "weak_evidence"
    HYPE = "hype"
    SENSITIVE_AUTOMATION = "sensitive_automation"


class ImmuneAction(StrEnum):
    SLOW = "slow"
    LABEL = "label"
    QUARANTINE = "quarantine"
    SCRUB = "scrub"
    TEST = "test"
    VALIDATE = "validate"
    HOLD = "hold"


@dataclass(frozen=True)
class CanonImmuneDecision:
    signal: CanonSignal
    action: ImmuneAction
    reason: str
    safe_next_action: str


def respond_to_canon_signal(signal: CanonSignal) -> CanonImmuneDecision:
    mapping = {
        CanonSignal.OVERCLAIM: CanonImmuneDecision(signal, ImmuneAction.LABEL, "Claim strength exceeds evidence.", "Downgrade R/P/C label and require ProofLadder target."),
        CanonSignal.IRREVERSIBLE_CHANGE: CanonImmuneDecision(signal, ImmuneAction.HOLD, "Irreversible change cannot be zero-touch.", "Hold action; require explicit validation and rollback or compensation plan."),
        CanonSignal.SENSITIVE_DATA: CanonImmuneDecision(signal, ImmuneAction.SCRUB, "Sensitive data detected.", "Scrub, quarantine, or move to private review."),
        CanonSignal.QUALIFIED_REVIEW_DOMAIN: CanonImmuneDecision(signal, ImmuneAction.HOLD, "Qualified review domain detected.", "Do not automate decision; route to appropriate qualified review."),
        CanonSignal.WEAK_EVIDENCE: CanonImmuneDecision(signal, ImmuneAction.TEST, "Evidence is too weak for stronger canon status.", "Add tests, baselines, measurements, or sources."),
        CanonSignal.HYPE: CanonImmuneDecision(signal, ImmuneAction.SLOW, "Language is hotter than evidence.", "Cool through RealityAnchor, OAK, and M- notes."),
        CanonSignal.SENSITIVE_AUTOMATION: CanonImmuneDecision(signal, ImmuneAction.VALIDATE, "Automation touches sensitive external domain.", "Use dry-run or one-touch validation; no autonomous external execution."),
    }
    return mapping[signal]
