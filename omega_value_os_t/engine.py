"""OAK judiciary and portfolio evaluator for Ω-VALUE-OS-T∞."""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .constitution import CONTEXT_PROFILES, constitution_payload
from .models import (
    AutonomyLevel,
    DecisionReport,
    DecisionStatus,
    HARD_GATES,
    ValueCase,
    canonical_json,
    stable_digest,
)
from .scoring import claim_ceiling, effective_value, opportunity_costs, pareto_frontier


AUTHORITY = "review_only"


def _gate_failures(case: ValueCase) -> list[str]:
    failed = [name for name in HARD_GATES if not bool(case.hard_gates.get(name))]
    ceiling = claim_ceiling(case)
    if case.claim_strength > ceiling + 1e-12:
        failed.append("claim_ceiling")
    if case.autonomy_level >= AutonomyLevel.A4_BOUNDED_CONSEQUENCE and not case.human_approval:
        failed.append("high_consequence_human_approval")
    if case.autonomy_level >= AutonomyLevel.A3_REVERSIBLE_EXECUTION and case.reversibility < 0.50:
        failed.append("insufficient_reversibility_for_autonomy")
    return sorted(set(failed))


def _warnings(case: ValueCase) -> list[str]:
    warnings: list[str] = []
    if not case.falsifiers:
        warnings.append("No explicit falsifier supplied; scientific promotion should remain conservative.")
    if not case.provenance_refs:
        warnings.append("No detailed provenance reference supplied beyond the hard-gate declaration.")
    if case.uncertainty >= 0.70:
        warnings.append("High declared uncertainty; prefer information-gathering actions.")
    if case.closure < 0.50:
        warnings.append("Crystallization debt risk: artifact closure is below 0.50.")
    if case.evidence_level.value <= 1:
        warnings.append("Evidence remains internal/self-generated; external validation is absent.")
    return warnings


def evaluate_case(case: ValueCase) -> DecisionReport:
    if case.profile not in CONTEXT_PROFILES:
        raise ValueError(f"unknown context profile: {case.profile}")
    profile = CONTEXT_PROFILES[case.profile]
    failures = _gate_failures(case)
    values = effective_value(case, profile)
    ceiling = claim_ceiling(case)
    respected = case.claim_strength <= ceiling + 1e-12
    warnings = _warnings(case)

    if failures:
        status = DecisionStatus.BLOCKED
        next_action = "Resolve non-compensable gate failures before further promotion or action."
    elif case.evidence_strength < profile.evidence_floor and case.expected_information_value > case.expected_action_value:
        status = DecisionStatus.ABSTAIN
        next_action = "Acquire the highest-information low-cost evidence before acting; abstention is the valid result."
    elif (
        case.evidence_level.value >= profile.human_review_external_evidence_floor
        and case.closure >= profile.human_review_closure_floor
        and case.evidence_strength >= profile.evidence_floor
    ):
        status = DecisionStatus.ELIGIBLE_FOR_HUMAN_REVIEW
        next_action = "Prepare a bounded human review packet; this engine grants no merge, publication or external authority."
    else:
        status = DecisionStatus.ELIGIBLE_FOR_EXPERIMENT
        next_action = "Run the smallest discriminating falsification/benchmark experiment and record M± evidence."

    if case.autonomy_level >= AutonomyLevel.A3_REVERSIBLE_EXECUTION:
        warnings.append("A3+ intent detected; this package evaluates only and performs no external action.")

    provisional = DecisionReport(
        case_id=case.case_id,
        status=status,
        profile=case.profile,
        hard_gate_passed=not failures,
        failed_gates=tuple(failures),
        warnings=tuple(sorted(set(warnings))),
        soft_score=values["soft_score"],
        debt_penalty=values["debt_penalty"],
        external_evidence_factor=values["external_evidence_factor"],
        closure_factor=values["closure_factor"],
        reuse_factor=values["reuse_factor"],
        effective_value=values["effective_value"] if not failures else 0.0,
        claim_ceiling=ceiling,
        claim_ceiling_respected=respected,
        authority=AUTHORITY,
        human_review_required=True,
        next_action=next_action,
        input_digest=stable_digest(case.to_dict()),
    )
    digest = stable_digest(provisional.payload(include_digest=False))
    return replace(provisional, report_digest=digest)


def evaluate_portfolio(cases: Iterable[ValueCase]) -> dict:
    cases = tuple(cases)
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("portfolio case_id values must be unique")
    reports = [evaluate_case(case) for case in cases]
    score_by_id = {report.case_id: report.effective_value for report in reports}
    soft_dimensions = ("truth", "evidence", "utility", "testability", "crystallization", "simplicity")
    frontier = pareto_frontier(cases, soft_dimensions)
    payload = {
        "system": "Ω-VALUE-OS-T∞",
        "version": "R0.1",
        "reports": [report.payload() for report in sorted(reports, key=lambda x: x.case_id)],
        "pareto_dimensions": list(soft_dimensions),
        "pareto_frontier": list(frontier),
        "opportunity_costs": opportunity_costs(score_by_id),
        "authority": AUTHORITY,
        "human_review_required": True,
        "automatic_merge_allowed": False,
        "automatic_publication_allowed": False,
        "external_action_performed": False,
        "scores_are_probabilities": False,
    }
    payload["portfolio_digest"] = stable_digest(payload)
    return payload


def oak_report() -> dict:
    payload = constitution_payload()
    payload["checks"] = {
        "hard_gates_non_compensatory": True,
        "claim_ceiling_enforced": True,
        "abstention_supported": True,
        "pareto_supported": True,
        "debt_penalty_supported": True,
        "context_weights_supported": True,
        "autonomy_authority_separated": True,
        "external_action_surface": False,
        "automatic_merge_surface": False,
        "automatic_publication_surface": False,
    }
    payload["oak_digest"] = stable_digest(payload)
    return payload


def dump_json(payload: object) -> str:
    return canonical_json(payload) + "\n"
