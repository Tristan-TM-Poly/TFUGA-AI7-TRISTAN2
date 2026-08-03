"""Risk debt ledger for Tristan AIT immune systems.

This module makes risk debt explicit. It is not medical, legal, financial, or
security advice. It is a conservative scoring helper for OAK-safe planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DebtSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RiskDebtItem:
    """One visible unit of risk debt."""

    name: str
    severity: DebtSeverity
    description: str
    mitigation: str
    points: int


@dataclass(frozen=True)
class RiskDebtReport:
    """Aggregated risk debt report."""

    total_points: int
    severity: DebtSeverity
    items: tuple[RiskDebtItem, ...] = field(default_factory=tuple)

    @property
    def blocks_zero_touch(self) -> bool:
        return self.severity in {DebtSeverity.HIGH, DebtSeverity.CRITICAL}


def classify_debt(points: int) -> DebtSeverity:
    if points >= 12:
        return DebtSeverity.CRITICAL
    if points >= 7:
        return DebtSeverity.HIGH
    if points >= 3:
        return DebtSeverity.MEDIUM
    return DebtSeverity.LOW


def assess_risk_debt(
    *,
    missing_tests: bool = False,
    weak_sources: bool = False,
    no_rollback: bool = False,
    sensitive_data_unclear: bool = False,
    irreversible_or_public_side_effect: bool = False,
    claim_too_strong: bool = False,
    uncertainty_unquantified: bool = False,
) -> RiskDebtReport:
    """Assess explicit risk debt for an action or theory.

    The scoring is intentionally conservative and simple. The goal is not exact
    risk prediction; the goal is to keep hidden shortcuts visible.
    """

    items: list[RiskDebtItem] = []

    def add(name: str, severity: DebtSeverity, description: str, mitigation: str, points: int) -> None:
        items.append(RiskDebtItem(name, severity, description, mitigation, points))

    if missing_tests:
        add(
            "missing_tests",
            DebtSeverity.MEDIUM,
            "The action/theory lacks verification tests.",
            "Add minimal tests, examples, or falsification cases.",
            3,
        )

    if weak_sources:
        add(
            "weak_sources",
            DebtSeverity.MEDIUM,
            "Sensitive claims are not tied to strong sources.",
            "Add official, primary, or high-trust sources and mark uncertainty.",
            3,
        )

    if no_rollback:
        add(
            "no_rollback",
            DebtSeverity.HIGH,
            "No rollback or compensation path is defined.",
            "Define RollbackProof before external execution or ZERO-TOUCH.",
            5,
        )

    if sensitive_data_unclear:
        add(
            "sensitive_data_unclear",
            DebtSeverity.HIGH,
            "Privacy/IP/secret classification is unclear.",
            "Run PrivacyGate and scrub or quarantine sensitive content.",
            5,
        )

    if irreversible_or_public_side_effect:
        add(
            "irreversible_or_public_side_effect",
            DebtSeverity.CRITICAL,
            "The action may be public, irreversible, destructive, or externally committing.",
            "Require ONE-TOUCH/NO-TOUCH and explicit validation.",
            7,
        )

    if claim_too_strong:
        add(
            "claim_too_strong",
            DebtSeverity.MEDIUM,
            "The language overstates proof, safety, or certainty.",
            "Downgrade claim status: vision, hypothesis, prototype, measured result, or proof.",
            3,
        )

    if uncertainty_unquantified:
        add(
            "uncertainty_unquantified",
            DebtSeverity.MEDIUM,
            "Important unknowns are not visible.",
            "Add uncertainty notes, assumptions, and residuals.",
            3,
        )

    total = sum(item.points for item in items)
    return RiskDebtReport(total_points=total, severity=classify_debt(total), items=tuple(items))
