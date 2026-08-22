"""Hard OAK gates for the Ω Value OS.

These gates are intentionally non-compensatory: a high expected return cannot
cancel a failed authority, compliance, evidence, or reversibility gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .models import AuthorityEnvelope, AutomationCandidate


SENSITIVE_ACTION_PREFIXES = (
    "payment",
    "transfer",
    "purchase",
    "contract",
    "tax",
    "legal",
    "pricing_major",
    "publish_sensitive",
    "authority_change",
    "credential_change",
)

PROHIBITED_AUTOMATION_PATTERNS = (
    "fake_engagement",
    "deceptive_claim",
    "dark_pattern",
    "permission_bypass",
    "policy_bypass",
)


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: Tuple[str, ...]


def is_sensitive_action(action: str) -> bool:
    normalized = action.strip().lower()
    return any(normalized.startswith(prefix) for prefix in SENSITIVE_ACTION_PREFIXES)


def evaluate_hard_gates(
    candidate: AutomationCandidate,
    envelope: AuthorityEnvelope,
) -> GateResult:
    reasons = []
    action = candidate.action.strip().lower()

    if any(pattern in action for pattern in PROHIBITED_AUTOMATION_PATTERNS):
        reasons.append("constitution: prohibited manipulation or bypass pattern")

    if action not in envelope.allowed_actions:
        reasons.append("authority: action not present in allowed_actions")

    if action in envelope.requires_human_approval:
        reasons.append("authority: explicit human approval required")

    if candidate.estimated_cost > envelope.max_budget:
        reasons.append("budget: estimated cost exceeds authority envelope")

    if candidate.irreversibility > envelope.max_irreversibility:
        reasons.append("reversibility: irreversibility exceeds authority envelope")

    if is_sensitive_action(action):
        reasons.append("sensitivity: sensitive action cannot be zero-touch")

    if candidate.compliance_risk >= 0.5:
        reasons.append("compliance: risk too high for autonomous promotion")

    if candidate.model_uncertainty >= 0.7:
        reasons.append("uncertainty: model uncertainty too high")

    return GateResult(passed=not reasons, reasons=tuple(reasons))
