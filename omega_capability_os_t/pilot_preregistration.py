"""Bounded Québec preregistration court for Capability OS / Eighth Fire.

The purpose of this module is to freeze a real-world pilot protocol before
outcomes are observed. It does not create participants, fabricate evidence, or
grant deployment authority.

Core invariants:
- AcceptanceRate is diagnostic, never a success gate.
- SystemPerformedTask != BeneficiaryAcquiredCapability.
- ProcessPASS != AdoptionPASS != PermissionToDeploy.
- Criteria must be frozen before outcome observation.
- Material change requires reconsultation.
- Personalized psychological targeting is not an admissible adoption tactic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from omega_capability_os_t.core import stable_digest
from omega_capability_os_t.social_legitimacy_profile import FrozenLegitimacyCriteria
from omega_capability_os_t.virtual_tristan_8f import FrozenTransferCriteria


_REQUIRED_DECISIONS = {"HOLD", "REVISE", "NO_ACTION", "PILOT_ELIGIBLE"}
_PLACEHOLDER_MARKERS = ("TBD", "REPLACE_ME", "<FILL", "<REAL_", "__FILL__")


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        upper = value.upper()
        return any(marker in upper for marker in _PLACEHOLDER_MARKERS)
    if isinstance(value, dict):
        return any(_contains_placeholder(k) or _contains_placeholder(v) for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_placeholder(item) for item in value)
    return False


@dataclass(frozen=True)
class QuebecPilotPreregistration:
    protocol_id: str
    jurisdiction: str
    context: str
    affected_groups: tuple[str, ...]
    beneficiary_groups: tuple[str, ...]
    system_version: str
    consent_version: str
    generator_id: str
    evaluator_id: str
    baseline: str
    intervention: str
    alternatives: tuple[str, ...]
    transfer_observable: str
    withdrawal_condition: str
    delayed_replay_window: str
    dependency_measurement: str
    min_withdrawal_retention: float
    min_delayed_retention: float
    max_dependency_after_withdrawal: float
    min_understanding: float
    min_agency: float
    max_acceptance_debt: float
    opt_out_mechanism: str
    contestation_mechanism: str
    rollback_mechanism: str
    evidence_disclosure: str
    stakeholder_representation: str
    minority_residual_policy: str
    material_change_reconsultation: bool
    personalized_psychological_targeting: bool
    acceptance_rate_is_success_gate: bool
    outcomes_observed: bool
    authority_status: str
    decision_criteria: tuple[str, ...] = ("HOLD", "REVISE", "NO_ACTION", "PILOT_ELIGIBLE")
    require_delayed_above_baseline: bool = True
    require_evaluator_separation: bool = True

    def __post_init__(self) -> None:
        required_text = (
            "protocol_id",
            "jurisdiction",
            "context",
            "system_version",
            "consent_version",
            "generator_id",
            "evaluator_id",
            "baseline",
            "intervention",
            "transfer_observable",
            "withdrawal_condition",
            "delayed_replay_window",
            "dependency_measurement",
            "opt_out_mechanism",
            "contestation_mechanism",
            "rollback_mechanism",
            "evidence_disclosure",
            "stakeholder_representation",
            "minority_residual_policy",
            "authority_status",
        )
        for field_name in required_text:
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")

        if not self.affected_groups:
            raise ValueError("affected_groups must be non-empty")
        if not self.beneficiary_groups:
            raise ValueError("beneficiary_groups must be non-empty")

        values = (
            self.min_withdrawal_retention,
            self.min_delayed_retention,
            self.max_dependency_after_withdrawal,
            self.min_understanding,
            self.min_agency,
            self.max_acceptance_debt,
        )
        if any(not isfinite(float(value)) or float(value) < 0.0 for value in values):
            raise ValueError("pilot thresholds must be finite and >= 0")
        if self.min_understanding > 1.0 or self.min_agency > 1.0:
            raise ValueError("understanding and agency thresholds must be in [0, 1]")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuebecPilotPreregistration":
        return cls(
            protocol_id=str(payload["protocol_id"]),
            jurisdiction=str(payload["jurisdiction"]),
            context=str(payload["context"]),
            affected_groups=tuple(map(str, payload.get("affected_groups", []))),
            beneficiary_groups=tuple(map(str, payload.get("beneficiary_groups", []))),
            system_version=str(payload["system_version"]),
            consent_version=str(payload["consent_version"]),
            generator_id=str(payload["generator_id"]),
            evaluator_id=str(payload["evaluator_id"]),
            baseline=str(payload["baseline"]),
            intervention=str(payload["intervention"]),
            alternatives=tuple(map(str, payload.get("alternatives", []))),
            transfer_observable=str(payload["transfer_observable"]),
            withdrawal_condition=str(payload["withdrawal_condition"]),
            delayed_replay_window=str(payload["delayed_replay_window"]),
            dependency_measurement=str(payload["dependency_measurement"]),
            min_withdrawal_retention=float(payload["min_withdrawal_retention"]),
            min_delayed_retention=float(payload["min_delayed_retention"]),
            max_dependency_after_withdrawal=float(payload["max_dependency_after_withdrawal"]),
            min_understanding=float(payload["min_understanding"]),
            min_agency=float(payload["min_agency"]),
            max_acceptance_debt=float(payload["max_acceptance_debt"]),
            opt_out_mechanism=str(payload["opt_out_mechanism"]),
            contestation_mechanism=str(payload["contestation_mechanism"]),
            rollback_mechanism=str(payload["rollback_mechanism"]),
            evidence_disclosure=str(payload["evidence_disclosure"]),
            stakeholder_representation=str(payload["stakeholder_representation"]),
            minority_residual_policy=str(payload["minority_residual_policy"]),
            material_change_reconsultation=bool(payload["material_change_reconsultation"]),
            personalized_psychological_targeting=bool(payload["personalized_psychological_targeting"]),
            acceptance_rate_is_success_gate=bool(payload["acceptance_rate_is_success_gate"]),
            outcomes_observed=bool(payload["outcomes_observed"]),
            authority_status=str(payload["authority_status"]),
            decision_criteria=tuple(map(str, payload.get("decision_criteria", ()))),
            require_delayed_above_baseline=bool(payload.get("require_delayed_above_baseline", True)),
            require_evaluator_separation=bool(payload.get("require_evaluator_separation", True)),
        )

    def protocol_digest(self) -> str:
        return stable_digest(asdict(self))

    def legitimacy_criteria(self) -> FrozenLegitimacyCriteria:
        return FrozenLegitimacyCriteria(
            initiative_id=self.protocol_id,
            system_version=self.system_version,
            consent_version=self.consent_version,
            evaluator_id=self.evaluator_id,
            min_understanding=self.min_understanding,
            min_agency=self.min_agency,
            max_acceptance_debt=self.max_acceptance_debt,
            require_evaluator_separation=self.require_evaluator_separation,
            require_opt_out=True,
            require_contestability=True,
            require_reversibility=True,
            require_evidence_transparency=True,
            require_stakeholder_representation=True,
            forbid_personalized_manipulation=True,
        )

    def transfer_criteria(self) -> FrozenTransferCriteria:
        return FrozenTransferCriteria(
            experiment_id=self.protocol_id,
            evaluator_id=self.evaluator_id,
            min_withdrawal_retention=self.min_withdrawal_retention,
            min_delayed_retention=self.min_delayed_retention,
            max_dependency_after_withdrawal=self.max_dependency_after_withdrawal,
            require_delayed_above_baseline=self.require_delayed_above_baseline,
            require_evaluator_separation=self.require_evaluator_separation,
        )


@dataclass(frozen=True)
class PilotPreregistrationReceipt:
    decision: str
    blockers: tuple[str, ...]
    protocol_digest: str | None
    legitimacy_criteria_digest: str | None
    transfer_criteria_digest: str | None
    execution_eligible: bool
    oak_boundary: str = (
        "FROZEN means the supplied Québec pilot protocol is complete enough to preregister before outcomes. "
        "It does not establish legal/ethical authority, recruit participants, prove benefit, prove social legitimacy, "
        "or authorize deployment. Real execution still requires the applicable authority and real-world governance."
    )


def evaluate_preregistration(protocol: QuebecPilotPreregistration) -> PilotPreregistrationReceipt:
    blockers: list[str] = []
    payload = asdict(protocol)

    normalized_jurisdiction = protocol.jurisdiction.casefold()
    if "québec" not in normalized_jurisdiction and "quebec" not in normalized_jurisdiction:
        blockers.append("quebec_first_jurisdiction_required")
    if _contains_placeholder(payload):
        blockers.append("unresolved_placeholder")
    if protocol.outcomes_observed:
        blockers.append("outcomes_already_observed")
    if not protocol.alternatives:
        blockers.append("alternatives_missing")
    if protocol.require_evaluator_separation and protocol.generator_id == protocol.evaluator_id:
        blockers.append("generator_evaluator_not_separated")
    if not protocol.material_change_reconsultation:
        blockers.append("material_change_reconsultation_missing")
    if protocol.personalized_psychological_targeting:
        blockers.append("personalized_psychological_targeting_denied")
    if protocol.acceptance_rate_is_success_gate:
        blockers.append("acceptance_rate_cannot_be_success_gate")
    if not _REQUIRED_DECISIONS.issubset(set(protocol.decision_criteria)):
        blockers.append("decision_criteria_incomplete")

    decision = "FROZEN" if not blockers else "HOLD"
    protocol_digest = protocol.protocol_digest() if not blockers else None
    legitimacy_digest = protocol.legitimacy_criteria().digest() if not blockers else None
    transfer_digest = protocol.transfer_criteria().digest() if not blockers else None
    authority = protocol.authority_status.strip().upper()
    execution_eligible = decision == "FROZEN" and authority.startswith("AUTHORIZED")

    return PilotPreregistrationReceipt(
        decision=decision,
        blockers=tuple(sorted(set(blockers))),
        protocol_digest=protocol_digest,
        legitimacy_criteria_digest=legitimacy_digest,
        transfer_criteria_digest=transfer_digest,
        execution_eligible=execution_eligible,
    )
