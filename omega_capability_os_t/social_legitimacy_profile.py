"""Capability OS / Eighth-Fire social-legitimacy profile.

This is deliberately a profile/court, not a new runtime or persuasion engine.
It evaluates whether a proposed social deployment supports informed, voluntary,
contestable and reversible choice. Adoption rate is diagnostic only and can
never compensate for failed legitimacy gates.

OAK boundaries:
- Acceptance != legitimacy.
- Consensus != truth.
- Process PASS != permission to deploy.
- Personalization for accessibility/context != psychological manipulation.
- A legitimate process may end in adoption, rejection, revision, or no action.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

from omega_capability_os_t.core import stable_digest


@dataclass(frozen=True)
class FrozenLegitimacyCriteria:
    initiative_id: str
    system_version: str
    consent_version: str
    evaluator_id: str
    min_understanding: float = 0.70
    min_agency: float = 0.70
    max_acceptance_debt: float = 0.50
    require_evaluator_separation: bool = True
    require_opt_out: bool = True
    require_contestability: bool = True
    require_reversibility: bool = True
    require_evidence_transparency: bool = True
    require_stakeholder_representation: bool = True
    forbid_personalized_manipulation: bool = True

    def __post_init__(self) -> None:
        for field_name in ("initiative_id", "system_version", "consent_version", "evaluator_id"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        for value in (self.min_understanding, self.min_agency, self.max_acceptance_debt):
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError("legitimacy criteria values must be finite and >= 0")

    def digest(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True)
class SocialLegitimacyObservation:
    criteria_digest: str
    generator_id: str
    evaluator_id: str
    system_version: str
    consent_version: str
    understanding: float
    agency: float
    acceptance_rate: float
    non_coercion: bool
    opt_out_available: bool
    contestability_available: bool
    reversibility_available: bool
    evidence_transparent: bool
    stakeholder_representation_present: bool
    minority_residuals: tuple[str, ...] = ()
    minority_residuals_preserved: bool = True
    unresolved_concerns: float = 0.0
    information_asymmetry: float = 0.0
    hidden_dependency: float = 0.0
    unmeasured_harm: float = 0.0
    unrepresented_stakeholders: float = 0.0
    personalized_manipulation_used: bool = False
    material_change_since_consent: bool = False

    def __post_init__(self) -> None:
        for field_name in ("generator_id", "evaluator_id", "system_version", "consent_version"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        for value in (
            self.understanding,
            self.agency,
            self.acceptance_rate,
            self.unresolved_concerns,
            self.information_asymmetry,
            self.hidden_dependency,
            self.unmeasured_harm,
            self.unrepresented_stakeholders,
        ):
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError("legitimacy observations must be finite and >= 0")
        if self.acceptance_rate > 1.0:
            raise ValueError("acceptance_rate must be in [0, 1]")

    def acceptance_debt(self) -> float:
        return round(
            self.unresolved_concerns
            + self.information_asymmetry
            + self.hidden_dependency
            + self.unmeasured_harm
            + self.unrepresented_stakeholders,
            6,
        )


@dataclass(frozen=True)
class SocialLegitimacyReceipt:
    decision: str
    blockers: tuple[str, ...]
    acceptance_rate: float
    acceptance_debt: float
    minority_residuals: tuple[str, ...]
    criteria_digest: str
    oak_boundary: str = (
        "PASS means the supplied observation satisfies frozen social-legitimacy process criteria. "
        "It does not mean adoption is desirable, morally correct, causally beneficial, representative of every affected party, "
        "or authorized. A PASS may legitimately coexist with zero adoption."
    )


def evaluate_social_legitimacy(
    criteria: FrozenLegitimacyCriteria,
    observation: SocialLegitimacyObservation,
) -> SocialLegitimacyReceipt:
    """Evaluate earned legitimacy without optimizing acceptance itself."""

    blockers: list[str] = []
    expected_digest = criteria.digest()

    if observation.criteria_digest != expected_digest:
        blockers.append("criteria_digest_mismatch")
    if observation.system_version != criteria.system_version:
        blockers.append("system_version_mismatch")
    if observation.consent_version != criteria.consent_version:
        blockers.append("consent_version_mismatch")
    if observation.evaluator_id != criteria.evaluator_id:
        blockers.append("unexpected_evaluator")
    if criteria.require_evaluator_separation and observation.generator_id == observation.evaluator_id:
        blockers.append("generator_evaluator_not_separated")
    if observation.material_change_since_consent:
        blockers.append("reconsultation_required")

    if observation.understanding < criteria.min_understanding:
        blockers.append("insufficient_understanding")
    if observation.agency < criteria.min_agency:
        blockers.append("insufficient_agency")
    if not observation.non_coercion:
        blockers.append("coercion_or_undue_pressure_detected")
    if criteria.require_opt_out and not observation.opt_out_available:
        blockers.append("opt_out_missing")
    if criteria.require_contestability and not observation.contestability_available:
        blockers.append("contestability_missing")
    if criteria.require_reversibility and not observation.reversibility_available:
        blockers.append("reversibility_missing")
    if criteria.require_evidence_transparency and not observation.evidence_transparent:
        blockers.append("evidence_transparency_missing")
    if criteria.require_stakeholder_representation and not observation.stakeholder_representation_present:
        blockers.append("stakeholder_representation_missing")
    if observation.minority_residuals and not observation.minority_residuals_preserved:
        blockers.append("minority_residual_erased")
    if criteria.forbid_personalized_manipulation and observation.personalized_manipulation_used:
        blockers.append("personalized_manipulation_denied")

    debt = observation.acceptance_debt()
    if debt > criteria.max_acceptance_debt:
        blockers.append("acceptance_debt_exceeds_threshold")

    # Deliberate invariant: acceptance_rate is never a positive gate. A well-run
    # process where everyone freely rejects the proposal can still PASS.
    return SocialLegitimacyReceipt(
        decision="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
        acceptance_rate=round(observation.acceptance_rate, 6),
        acceptance_debt=debt,
        minority_residuals=tuple(observation.minority_residuals),
        criteria_digest=expected_digest,
    )
