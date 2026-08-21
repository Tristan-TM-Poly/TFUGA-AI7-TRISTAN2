"""Eighth-Fire governance court for Virtual Tristans.

This module evaluates whether a Virtual Tristan intervention leaves verified
capability with declared beneficiaries without hiding dependency, capture,
missing consent, or irreversible harm behind an aggregate score.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class EighthFireThresholds:
    min_capability_left_behind: float = 0.5
    min_autonomy_gain: float = 0.0
    min_reciprocity: float = 0.0
    max_dependency_created: float = 0.5
    max_capture_risk: float = 0.25
    max_irreversible_harm: float = 0.0
    max_dependency_half_life: float = 1.0

    def __post_init__(self) -> None:
        values = (
            self.min_capability_left_behind,
            self.min_autonomy_gain,
            self.min_reciprocity,
            self.max_dependency_created,
            self.max_capture_risk,
            self.max_irreversible_harm,
            self.max_dependency_half_life,
        )
        if any(not isfinite(float(v)) for v in values):
            raise ValueError("all thresholds must be finite")
        if any(float(v) < 0.0 for v in values):
            raise ValueError("all thresholds must be >= 0")


@dataclass(frozen=True)
class BeneficiaryFlow:
    beneficiary_id: str
    capability_left_behind: float
    autonomy_gain: float
    forkability_gain: float
    reciprocity: float
    dependency_created: float
    capture_risk: float
    irreversible_harm: float
    dependency_half_life: float
    consent_present: bool = False
    attribution_present: bool = False

    def __post_init__(self) -> None:
        if not self.beneficiary_id.strip():
            raise ValueError("beneficiary_id must be non-empty")
        vals = (
            self.capability_left_behind,
            self.autonomy_gain,
            self.forkability_gain,
            self.reciprocity,
            self.dependency_created,
            self.capture_risk,
            self.irreversible_harm,
            self.dependency_half_life,
        )
        if any(not isfinite(float(v)) for v in vals):
            raise ValueError("flow values must be finite")
        if any(float(v) < 0.0 for v in vals):
            raise ValueError("flow values must be >= 0")

    def diagnostic_score(self) -> float:
        """Non-authoritative diagnostic score; hard gates remain non-compensatory."""
        positive = (
            self.capability_left_behind
            + self.autonomy_gain
            + self.forkability_gain
            + self.reciprocity
        )
        negative = self.dependency_created + self.capture_risk + self.irreversible_harm
        return round(positive - negative, 6)


@dataclass(frozen=True)
class EighthFireFlowDecision:
    beneficiary_id: str
    decision: str
    blockers: tuple[str, ...]
    diagnostic_score: float
    apoptosis_ready: bool


@dataclass(frozen=True)
class EighthFireSwarmReport:
    decision: str
    expected_beneficiaries: tuple[str, ...]
    observed_beneficiaries: tuple[str, ...]
    forgotten_beneficiaries: tuple[str, ...]
    decisions: tuple[EighthFireFlowDecision, ...]
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means supplied beneficiary flows satisfy declared non-compensatory Eighth-Fire thresholds. "
        "It does not prove moral correctness, causal benefit, complete beneficiary discovery, or absence of unmeasured harms."
    )


def evaluate_beneficiary_flow(
    flow: BeneficiaryFlow,
    thresholds: EighthFireThresholds = EighthFireThresholds(),
) -> EighthFireFlowDecision:
    blockers: list[str] = []
    if not flow.consent_present:
        blockers.append("consent_missing")
    if not flow.attribution_present:
        blockers.append("attribution_missing")
    if flow.capability_left_behind < thresholds.min_capability_left_behind:
        blockers.append("insufficient_capability_left_behind")
    if flow.autonomy_gain < thresholds.min_autonomy_gain:
        blockers.append("insufficient_autonomy_gain")
    if flow.reciprocity < thresholds.min_reciprocity:
        blockers.append("insufficient_reciprocity")
    if flow.dependency_created > thresholds.max_dependency_created:
        blockers.append("dependency_exceeds_threshold")
    if flow.capture_risk > thresholds.max_capture_risk:
        blockers.append("capture_risk_exceeds_threshold")
    if flow.irreversible_harm > thresholds.max_irreversible_harm:
        blockers.append("irreversible_harm_exceeds_threshold")
    if flow.dependency_half_life > thresholds.max_dependency_half_life:
        blockers.append("dependency_half_life_exceeds_threshold")

    apoptosis_ready = (
        not blockers
        and flow.capability_left_behind >= thresholds.min_capability_left_behind
        and flow.dependency_created == 0.0
        and flow.dependency_half_life == 0.0
    )
    return EighthFireFlowDecision(
        beneficiary_id=flow.beneficiary_id,
        decision="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
        diagnostic_score=flow.diagnostic_score(),
        apoptosis_ready=apoptosis_ready,
    )


def eighth_fire_swarm_court(
    flows: Iterable[BeneficiaryFlow],
    *,
    expected_beneficiaries: Iterable[str],
    thresholds: EighthFireThresholds = EighthFireThresholds(),
) -> EighthFireSwarmReport:
    rows = tuple(flows)
    expected = tuple(sorted({str(x).strip() for x in expected_beneficiaries if str(x).strip()}))
    observed = tuple(sorted({row.beneficiary_id for row in rows}))
    forgotten = tuple(sorted(set(expected) - set(observed)))
    decisions = tuple(evaluate_beneficiary_flow(row, thresholds) for row in rows)

    blockers: list[str] = []
    if not expected:
        blockers.append("expected_beneficiaries_missing")
    if forgotten:
        blockers.append("beneficiary_n_plus_one_failure")
    if len(observed) != len(rows):
        blockers.append("duplicate_beneficiary_flow")
    if any(d.decision != "PASS" for d in decisions):
        blockers.append("beneficiary_flow_gate_failed")

    return EighthFireSwarmReport(
        decision="PASS" if not blockers else "HOLD",
        expected_beneficiaries=expected,
        observed_beneficiaries=observed,
        forgotten_beneficiaries=forgotten,
        decisions=decisions,
        blockers=tuple(sorted(set(blockers))),
    )
