"""Eighth-Fire governance court for Virtual Tristans.

This module evaluates whether a Virtual Tristan intervention leaves verified
capability with declared beneficiaries without hiding dependency, capture,
missing consent, or irreversible harm behind an aggregate score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable

from omega_capability_os_t.core import stable_digest


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


# R0.4: constitutional projection and prospective proof-of-transfer.
# These objects extend the existing beneficiary-flow court rather than creating
# a second Eighth-Fire runtime or a new agent ontology.


@dataclass(frozen=True)
class ConstitutionalGates:
    evidence: bool
    safety: bool
    non_domination: bool
    regeneration: bool
    rollback_contestability: bool

    def blockers(self) -> tuple[str, ...]:
        checks = {
            "evidence_gate_failed": self.evidence,
            "safety_gate_failed": self.safety,
            "non_domination_gate_failed": self.non_domination,
            "regeneration_gate_failed": self.regeneration,
            "rollback_contestability_gate_failed": self.rollback_contestability,
        }
        return tuple(sorted(name for name, passed in checks.items() if not passed))


@dataclass(frozen=True)
class ConstitutionalFlowDecision:
    beneficiary_id: str
    decision: str
    blockers: tuple[str, ...]
    diagnostic_score: float
    apoptosis_ready: bool
    oak_boundary: str = (
        "PASS means the supplied beneficiary flow and explicitly supplied constitutional gates pass. "
        "It does not establish moral truth, cultural authority, causal benefit, permission to act, or complete harm discovery."
    )


def evaluate_constitutional_beneficiary_flow(
    flow: BeneficiaryFlow,
    gates: ConstitutionalGates,
    thresholds: EighthFireThresholds = EighthFireThresholds(),
) -> ConstitutionalFlowDecision:
    base = evaluate_beneficiary_flow(flow, thresholds)
    blockers = tuple(sorted(set(base.blockers + gates.blockers())))
    return ConstitutionalFlowDecision(
        beneficiary_id=flow.beneficiary_id,
        decision="PASS" if not blockers else "HOLD",
        blockers=blockers,
        diagnostic_score=base.diagnostic_score,
        apoptosis_ready=base.apoptosis_ready and not blockers,
    )


@dataclass(frozen=True)
class FrozenTransferCriteria:
    experiment_id: str
    evaluator_id: str
    min_withdrawal_retention: float = 0.70
    min_delayed_retention: float = 0.60
    max_dependency_after_withdrawal: float = 0.0
    require_delayed_above_baseline: bool = True
    require_evaluator_separation: bool = True

    def __post_init__(self) -> None:
        if not self.experiment_id.strip() or not self.evaluator_id.strip():
            raise ValueError("experiment_id and evaluator_id must be non-empty")
        values = (
            self.min_withdrawal_retention,
            self.min_delayed_retention,
            self.max_dependency_after_withdrawal,
        )
        if any(not isfinite(float(v)) for v in values):
            raise ValueError("transfer criteria values must be finite")
        if any(float(v) < 0.0 for v in values):
            raise ValueError("transfer criteria values must be >= 0")

    def digest(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True)
class TransferObservation:
    beneficiary_id: str
    criteria_digest: str
    generator_id: str
    evaluator_id: str
    baseline_capability: float
    assisted_capability: float
    withdrawal_capability: float
    delayed_capability: float
    dependency_after_withdrawal: float
    system_available_during_withdrawal: bool = False

    def __post_init__(self) -> None:
        for value in (
            self.baseline_capability,
            self.assisted_capability,
            self.withdrawal_capability,
            self.delayed_capability,
            self.dependency_after_withdrawal,
        ):
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError("transfer observations must be finite and >= 0")
        if not self.beneficiary_id.strip():
            raise ValueError("beneficiary_id must be non-empty")
        if not self.generator_id.strip() or not self.evaluator_id.strip():
            raise ValueError("generator_id and evaluator_id must be non-empty")


@dataclass(frozen=True)
class TransferEvidenceReceipt:
    beneficiary_id: str
    decision: str
    withdrawal_retention: float | None
    delayed_retention: float | None
    delayed_gain_over_baseline: float
    dependency_after_withdrawal: float
    blockers: tuple[str, ...]
    criteria_digest: str
    oak_boundary: str = (
        "PASS means one supplied finite observation satisfies frozen transfer criteria after declared system withdrawal. "
        "It does not establish randomized causal effect, universal independence, long-term empowerment, complete beneficiary discovery, "
        "or permission to deploy or expand."
    )


def evaluate_prospective_transfer(
    criteria: FrozenTransferCriteria,
    observation: TransferObservation,
) -> TransferEvidenceReceipt:
    expected_digest = criteria.digest()
    blockers: list[str] = []
    if observation.criteria_digest != expected_digest:
        blockers.append("criteria_digest_mismatch")
    if observation.evaluator_id != criteria.evaluator_id:
        blockers.append("unexpected_evaluator")
    if criteria.require_evaluator_separation and observation.generator_id == observation.evaluator_id:
        blockers.append("generator_evaluator_not_separated")
    if observation.system_available_during_withdrawal:
        blockers.append("system_not_withdrawn")
    if observation.dependency_after_withdrawal > criteria.max_dependency_after_withdrawal:
        blockers.append("dependency_after_withdrawal_exceeds_threshold")

    withdrawal_retention: float | None = None
    delayed_retention: float | None = None
    if observation.assisted_capability <= 0.0:
        blockers.append("assisted_capability_not_positive")
    else:
        withdrawal_retention = observation.withdrawal_capability / observation.assisted_capability
        delayed_retention = observation.delayed_capability / observation.assisted_capability
        if withdrawal_retention < criteria.min_withdrawal_retention:
            blockers.append("insufficient_withdrawal_retention")
        if delayed_retention < criteria.min_delayed_retention:
            blockers.append("insufficient_delayed_retention")

    delayed_gain = observation.delayed_capability - observation.baseline_capability
    if criteria.require_delayed_above_baseline and delayed_gain <= 0.0:
        blockers.append("no_delayed_gain_over_baseline")

    return TransferEvidenceReceipt(
        beneficiary_id=observation.beneficiary_id,
        decision="PASS" if not blockers else "HOLD",
        withdrawal_retention=None if withdrawal_retention is None else round(withdrawal_retention, 6),
        delayed_retention=None if delayed_retention is None else round(delayed_retention, 6),
        delayed_gain_over_baseline=round(delayed_gain, 6),
        dependency_after_withdrawal=observation.dependency_after_withdrawal,
        blockers=tuple(sorted(set(blockers))),
        criteria_digest=expected_digest,
    )
