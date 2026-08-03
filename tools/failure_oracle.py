"""Failure Oracle for Tristan AIT Reality Forge.

Predicts plausible failure modes before action. This is a conservative planning
helper, not an oracle of truth or a substitute for domain experts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FailureMode:
    name: str
    severity: FailureSeverity
    trigger: str
    mitigation: str
    requires_no_touch: bool = False


@dataclass(frozen=True)
class FailureOracleReport:
    idea: str
    modes: tuple[FailureMode, ...]
    highest_severity: FailureSeverity
    no_touch_required: bool


RISK_TERMS = {
    "medical": FailureMode("medical_boundary", FailureSeverity.CRITICAL, "medical context", "route to qualified medical help / BioTox", True),
    "dose": FailureMode("substance_optimization", FailureSeverity.CRITICAL, "dose/substance context", "refuse optimization and route safety", True),
    "delete": FailureMode("destructive_action", FailureSeverity.CRITICAL, "deletion/destructive action", "require NO-TOUCH or explicit rollback review", True),
    "publish": FailureMode("public_side_effect", FailureSeverity.HIGH, "public release", "require ONE-TOUCH, privacy/IP review", False),
    "secret": FailureMode("secret_leak", FailureSeverity.HIGH, "secret or credential mention", "scrub and block public commit", False),
    "guaranteed": FailureMode("overclaim", FailureSeverity.MEDIUM, "overconfident language", "downgrade claim level", False),
    "no tests": FailureMode("missing_tests", FailureSeverity.MEDIUM, "missing tests", "add tests before claim upgrade", False),
    "autonomous": FailureMode("autonomy_pressure", FailureSeverity.MEDIUM, "autonomy pressure", "apply AutonomyGate", False),
}


def _rank(severity: FailureSeverity) -> int:
    return {
        FailureSeverity.LOW: 0,
        FailureSeverity.MEDIUM: 1,
        FailureSeverity.HIGH: 2,
        FailureSeverity.CRITICAL: 3,
    }[severity]


def predict_failure_modes(idea: str) -> FailureOracleReport:
    normalized = idea.lower()
    modes: list[FailureMode] = []

    for term, mode in RISK_TERMS.items():
        if term in normalized:
            modes.append(mode)

    if not modes:
        modes.append(
            FailureMode(
                "unknown_unknowns",
                FailureSeverity.LOW,
                "no explicit risk term detected",
                "still require RealityAnchor, tests, and rollback before stronger claims",
            )
        )

    highest = max((mode.severity for mode in modes), key=_rank)
    no_touch = any(mode.requires_no_touch for mode in modes)
    return FailureOracleReport(idea=idea, modes=tuple(modes), highest_severity=highest, no_touch_required=no_touch)
