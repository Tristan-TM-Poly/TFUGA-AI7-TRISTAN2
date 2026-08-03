"""Non-compensatory OAK gates for synergy constellations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .contracts import GateDecision, GateStatus, SynergyConstellation


@dataclass(slots=True)
class GatePolicy:
    min_interface_count: int = 1
    min_baseline_count: int = 1
    min_metric_count: int = 1
    min_falsifier_count: int = 1
    min_rollback_count: int = 1
    min_evidence_for_human_review: float = 0.55
    max_risk_for_unisolated_experiment: float = 0.75
    max_uncertainty_for_human_review: float = 0.70
    require_simplest_baseline: bool = True
    require_provenance: bool = True
    require_named_evidence_for_human_review: bool = True
    block_recursive_without_governor: bool = True
    critical_keywords: tuple[str, ...] = (
        "security", "secret", "financial", "medical", "legal", "public",
        "publication", "release", "merge", "deployment", "patent",
    )

    def __post_init__(self) -> None:
        for name in ("min_interface_count", "min_baseline_count", "min_metric_count", "min_falsifier_count", "min_rollback_count"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        for name in ("min_evidence_for_human_review", "max_risk_for_unisolated_experiment", "max_uncertainty_for_human_review"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


def _has_simplest_baseline(constellation: SynergyConstellation) -> bool:
    normalized = " ".join(constellation.baselines).lower()
    return any(token in normalized for token in ("simplest", "single-system", "single system", "baseline_a", "baseline a"))


def _critical_scope(constellation: SynergyConstellation, policy: GatePolicy) -> bool:
    text = " ".join([constellation.name, constellation.objective, *constellation.risks, *constellation.domains]).lower()
    return any(keyword in text for keyword in policy.critical_keywords)


def evaluate_constellation(
    constellation: SynergyConstellation,
    *,
    policy: GatePolicy | None = None,
    available_evidence: Sequence[str] = (),
    known_interfaces: Sequence[str] = (),
    governors: Sequence[str] = (),
) -> GateDecision:
    policy = policy or GatePolicy()
    satisfied: list[str] = []
    missing: list[str] = []
    next_actions: list[str] = []

    interfaces = set(constellation.required_interfaces) | set(known_interfaces)
    if len(interfaces) >= policy.min_interface_count:
        satisfied.append("typed_interface")
    else:
        missing.append("typed_interface")
        next_actions.append("define_minimal_loss_declaring_interface")

    if len(constellation.baselines) >= policy.min_baseline_count:
        satisfied.append("baseline")
    else:
        missing.append("baseline")
        next_actions.append("add_isolated_component_baselines")

    if not policy.require_simplest_baseline or _has_simplest_baseline(constellation):
        satisfied.append("simplest_baseline")
    else:
        missing.append("simplest_baseline")
        next_actions.append("add_simplest_solution_baseline")

    if len(constellation.metrics) >= policy.min_metric_count:
        satisfied.append("metrics")
    else:
        missing.append("metrics")
        next_actions.append("define_observable_metrics")

    if len(constellation.falsifiers) >= policy.min_falsifier_count:
        satisfied.append("falsifier")
    else:
        missing.append("falsifier")
        next_actions.append("define_failure_and_counterexample_conditions")

    if len(constellation.rollback) >= policy.min_rollback_count:
        satisfied.append("rollback")
    else:
        missing.append("rollback")
        next_actions.append("define_reversible_rollback")

    provenance_present = bool(constellation.metadata.get("provenance") or constellation.evidence_refs)
    if not policy.require_provenance or provenance_present:
        satisfied.append("provenance")
    else:
        missing.append("provenance")
        next_actions.append("attach_source_heads_and_locators")

    named_evidence = sorted(set(constellation.evidence_refs) & set(available_evidence))
    if constellation.evidence_strength > 0 and named_evidence:
        satisfied.append("named_evidence")
    elif constellation.evidence_strength <= 0:
        missing.append("evidence_strength")
        next_actions.append("run_baseline_and_collect_evidence")
    else:
        missing.append("named_evidence")
        next_actions.append("attach_named_evidence_bundle")

    critical_scope = _critical_scope(constellation, policy)
    isolated = bool(constellation.metadata.get("isolated_sandbox"))
    if constellation.risk_score <= policy.max_risk_for_unisolated_experiment or isolated:
        satisfied.append("risk_isolated")
    else:
        missing.append("risk_isolation")
        next_actions.append("isolate_sensitive_scope_in_sandbox")

    recursive = bool(constellation.metadata.get("recursive_generation"))
    governor_present = any(token.lower() in " ".join(governors).lower() for token in ("portfolio", "proof", "stopgate", "oak", "governor"))
    if not recursive or not policy.block_recursive_without_governor or governor_present:
        satisfied.append("recursive_governance")
    else:
        missing.append("recursive_governance")
        next_actions.append("attach_portfolio_proof_and_stop_governors")

    sensitive_human_gate = not critical_scope or bool(constellation.metadata.get("human_gate_explicit"))
    if sensitive_human_gate:
        satisfied.append("sensitive_human_gate")
    else:
        missing.append("sensitive_human_gate")
        next_actions.append("declare_human_gate_for_sensitive_actions")

    experiment_blockers = {
        "typed_interface", "baseline", "simplest_baseline", "metrics", "falsifier",
        "rollback", "provenance", "risk_isolation", "recursive_governance", "sensitive_human_gate",
    }
    status = GateStatus.BLOCKED if experiment_blockers & set(missing) else GateStatus.ELIGIBLE_FOR_EXPERIMENT
    review_requirements_met = (
        status == GateStatus.ELIGIBLE_FOR_EXPERIMENT
        and constellation.evidence_strength >= policy.min_evidence_for_human_review
        and constellation.uncertainty <= policy.max_uncertainty_for_human_review
        and (not policy.require_named_evidence_for_human_review or bool(named_evidence))
    )
    if review_requirements_met:
        status = GateStatus.ELIGIBLE_FOR_HUMAN_REVIEW
        satisfied.append("human_review_threshold")
    elif status != GateStatus.BLOCKED:
        next_actions.append("execute_bounded_experiment_before_promotion")

    rationale = (
        "Hard gates are evaluated before heuristic utility. "
        f"status={status.value}; satisfied={len(set(satisfied))}; missing={len(set(missing))}. "
        "Eligibility is not authority to merge, publish, release, spend, contact or certify."
    )
    return GateDecision(
        constellation_id=constellation.id,
        status=status,
        satisfied_gates=satisfied,
        missing_gates=missing,
        evidence_refs=named_evidence,
        next_actions=next_actions,
        rationale=rationale,
    )


def decision_index(decisions: Sequence[GateDecision]) -> dict[str, GateDecision]:
    return {decision.constellation_id: decision for decision in decisions}


def summarize_decisions(decisions: Sequence[GateDecision]) -> dict[str, int]:
    counts = {status.value: 0 for status in GateStatus}
    for decision in decisions:
        counts[decision.status.value] += 1
    counts["total"] = len(decisions)
    return counts
