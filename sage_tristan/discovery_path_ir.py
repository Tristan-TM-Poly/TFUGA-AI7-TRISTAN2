"""Ω-DISCOVERY-PATH-COMPILER-T∞ — R0.4 Discovery Path IR.

The fundamental object is a falsifiable trajectory between epistemic states,
not a claim to reproduce a historical person's mind.  A path records which
operators were applied, which evidence was admitted, how representations
changed, what residuals remained, and what resource/epistemic costs were paid.

Historical paths are reconstructions unless independently source-certified.
Software audits certify only the encoded invariants, never historical truth.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, Sequence

from sage_tristan.greatsages import ClaimClass, SageProfile, discovery_by_id, get_profile
from sage_tristan.greatsages_time_machine import (
    EpistemicDebt,
    causal_leakage_firewall,
    default_context,
    epistemic_debt_for_discovery,
    operator_registry,
    time_machine_snapshot,
)


class PathStatus(str, Enum):
    VALID_SOFTWARE_MODEL = "valid_software_model"
    QUARANTINE = "quarantine"


class PathMutation(str, Enum):
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    SWAP = "swap"
    REPRESENTATION = "representation"
    COUNTER = "counter"


@dataclass(frozen=True, slots=True)
class ResourceCost:
    compute: float = 0.0
    conceptual: float = 0.0
    evidence: float = 0.0
    uncertainty: float = 0.0
    epistemic_debt: float = 0.0
    representation_loss: float = 0.0
    risk: float = 0.0

    def __post_init__(self) -> None:
        if any(value < 0 for value in asdict(self).values()):
            raise ValueError("resource costs must be non-negative")

    @property
    def total(self) -> float:
        return round(
            self.compute
            + self.conceptual
            + self.evidence
            + 1.25 * self.uncertainty
            + 1.25 * self.epistemic_debt
            + 1.10 * self.representation_loss
            + 1.25 * self.risk,
            6,
        )


@dataclass(frozen=True, slots=True)
class ResidualVector:
    logical: float = 0.0
    empirical: float = 0.0
    representation: float = 0.0
    provenance: float = 0.0
    uncertainty: float = 0.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} residual must be in [0, 1]")

    @property
    def norm_l1(self) -> float:
        return round(sum(asdict(self).values()), 6)


@dataclass(frozen=True, slots=True)
class EpistemicState:
    state_id: str
    year: int
    knowledge_ids: tuple[str, ...]
    representation_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    open_problem_ids: tuple[str, ...] = ()
    uncertainty: float = 0.5
    epistemic_debt: float = 0.0
    provenance_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("state uncertainty must be in [0, 1]")
        if self.epistemic_debt < 0:
            raise ValueError("state epistemic debt must be non-negative")
        if len(self.knowledge_ids) != len(set(self.knowledge_ids)):
            raise ValueError("duplicate knowledge ids in epistemic state")


@dataclass(frozen=True, slots=True)
class PathStep:
    step_id: str
    operator_id: str
    input_state_id: str
    output_state_id: str
    year: int
    representation_before: tuple[str, ...] = ()
    representation_after: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    produced_claim_ids: tuple[str, ...] = ()
    cost: ResourceCost = ResourceCost()
    residuals: ResidualVector = ResidualVector()
    uncertainty_before: float = 0.5
    uncertainty_after: float = 0.5
    note: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("uncertainty_before", self.uncertainty_before),
            ("uncertainty_after", self.uncertainty_after),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")

    @property
    def uncertainty_delta(self) -> float:
        return round(self.uncertainty_after - self.uncertainty_before, 6)


@dataclass(frozen=True, slots=True)
class DiscoveryPath:
    path_id: str
    sage_id: str
    target_discovery_id: str
    claim_class: ClaimClass
    states: tuple[EpistemicState, ...]
    steps: tuple[PathStep, ...]
    source_ids: tuple[str, ...] = ()
    counterfactual: bool = False

    def __post_init__(self) -> None:
        if len(self.states) < 2:
            raise ValueError("a discovery path requires at least two states")
        if len(self.steps) != len(self.states) - 1:
            raise ValueError("steps must connect every adjacent state exactly once")
        state_ids = [state.state_id for state in self.states]
        step_ids = [step.step_id for step in self.steps]
        if len(state_ids) != len(set(state_ids)):
            raise ValueError("duplicate state id")
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("duplicate step id")

    @property
    def initial_state(self) -> EpistemicState:
        return self.states[0]

    @property
    def terminal_state(self) -> EpistemicState:
        return self.states[-1]

    @property
    def total_cost(self) -> float:
        return round(sum(step.cost.total for step in self.steps), 6)

    @property
    def residual_budget(self) -> float:
        return round(sum(step.residuals.norm_l1 for step in self.steps), 6)

    @property
    def lineage_hash(self) -> str:
        payload = {
            "path_id": self.path_id,
            "sage_id": self.sage_id,
            "target_discovery_id": self.target_discovery_id,
            "claim_class": self.claim_class.value,
            "states": [asdict(state) for state in self.states],
            "steps": [asdict(step) for step in self.steps],
            "source_ids": self.source_ids,
            "counterfactual": self.counterfactual,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PathAudit:
    path_id: str
    status: PathStatus
    continuity_valid: bool
    years_monotone: bool
    operators_known: bool
    initial_target_withheld: bool
    evidence_leakage_free: bool
    terminal_contains_target: bool
    uncertainty_nonincreasing: bool
    failures: tuple[str, ...]
    total_cost: float
    residual_budget: float
    historical_truth_certified: bool = False


@dataclass(frozen=True, slots=True)
class PathDiff:
    left_path_id: str
    right_path_id: str
    shared_operator_ids: tuple[str, ...]
    left_only_operator_ids: tuple[str, ...]
    right_only_operator_ids: tuple[str, ...]
    shared_representations: tuple[str, ...]
    cost_delta_right_minus_left: float
    residual_delta_right_minus_left: float


@dataclass(frozen=True, slots=True)
class ComposedPathReceipt:
    left_path_id: str
    right_path_id: str
    composed_path_id: str
    boundary_state_id: str
    lineage_hash: str


def _state_lookup(path: DiscoveryPath) -> Mapping[str, EpistemicState]:
    return {state.state_id: state for state in path.states}


def audit_path(profile: SageProfile, path: DiscoveryPath) -> PathAudit:
    discovery_by_id(profile, path.target_discovery_id)
    registry = operator_registry(profile)
    failures: list[str] = []

    continuity_valid = True
    for index, step in enumerate(path.steps):
        expected_in = path.states[index].state_id
        expected_out = path.states[index + 1].state_id
        if step.input_state_id != expected_in or step.output_state_id != expected_out:
            continuity_valid = False
            failures.append(f"step {step.step_id} breaks state continuity")

    years = [state.year for state in path.states]
    years_monotone = years == sorted(years) and all(
        path.states[index].year <= step.year <= path.states[index + 1].year
        for index, step in enumerate(path.steps)
    )
    if not years_monotone:
        failures.append("path years are not monotone")

    unknown = sorted({step.operator_id for step in path.steps} - set(registry))
    operators_known = not unknown
    if unknown:
        failures.append(f"unknown operators: {unknown}")

    initial_target_withheld = path.target_discovery_id not in set(path.initial_state.knowledge_ids)
    if not initial_target_withheld:
        failures.append("target discovery appears in initial state")

    firewall = causal_leakage_firewall(
        profile,
        path.target_discovery_id,
        year=path.initial_state.year,
    )
    forbidden = set(firewall.masked_discovery_ids)
    leaked = sorted(
        evidence
        for step in path.steps
        for evidence in step.evidence_ids
        if evidence in forbidden
    )
    evidence_leakage_free = not leaked
    if leaked:
        failures.append(f"post-gate/target evidence leaked into path: {leaked}")

    terminal_contains_target = path.target_discovery_id in set(path.terminal_state.knowledge_ids)
    if not terminal_contains_target:
        failures.append("terminal state does not contain target discovery")

    uncertainty_nonincreasing = path.terminal_state.uncertainty <= path.initial_state.uncertainty
    if not uncertainty_nonincreasing:
        failures.append("terminal uncertainty exceeds initial uncertainty")

    return PathAudit(
        path_id=path.path_id,
        status=PathStatus.VALID_SOFTWARE_MODEL if not failures else PathStatus.QUARANTINE,
        continuity_valid=continuity_valid,
        years_monotone=years_monotone,
        operators_known=operators_known,
        initial_target_withheld=initial_target_withheld,
        evidence_leakage_free=evidence_leakage_free,
        terminal_contains_target=terminal_contains_target,
        uncertainty_nonincreasing=uncertainty_nonincreasing,
        failures=tuple(failures),
        total_cost=path.total_cost,
        residual_budget=path.residual_budget,
    )


def compare_paths(left: DiscoveryPath, right: DiscoveryPath) -> PathDiff:
    left_ops = {step.operator_id for step in left.steps}
    right_ops = {step.operator_id for step in right.steps}
    left_reps = {rep for state in left.states for rep in state.representation_ids}
    right_reps = {rep for state in right.states for rep in state.representation_ids}
    return PathDiff(
        left_path_id=left.path_id,
        right_path_id=right.path_id,
        shared_operator_ids=tuple(sorted(left_ops & right_ops)),
        left_only_operator_ids=tuple(sorted(left_ops - right_ops)),
        right_only_operator_ids=tuple(sorted(right_ops - left_ops)),
        shared_representations=tuple(sorted(left_reps & right_reps)),
        cost_delta_right_minus_left=round(right.total_cost - left.total_cost, 6),
        residual_delta_right_minus_left=round(right.residual_budget - left.residual_budget, 6),
    )


def compose_paths(left: DiscoveryPath, right: DiscoveryPath, *, composed_path_id: str) -> tuple[DiscoveryPath, ComposedPathReceipt]:
    if left.sage_id != right.sage_id:
        raise ValueError("cannot compose paths with different sage/model scopes")
    if left.terminal_state != right.initial_state:
        raise ValueError("path boundary states must be identical for composition")
    composed = DiscoveryPath(
        path_id=composed_path_id,
        sage_id=left.sage_id,
        target_discovery_id=right.target_discovery_id,
        claim_class=right.claim_class,
        states=left.states + right.states[1:],
        steps=left.steps + right.steps,
        source_ids=tuple(dict.fromkeys(left.source_ids + right.source_ids)),
        counterfactual=left.counterfactual or right.counterfactual,
    )
    receipt = ComposedPathReceipt(
        left_path_id=left.path_id,
        right_path_id=right.path_id,
        composed_path_id=composed.path_id,
        boundary_state_id=left.terminal_state.state_id,
        lineage_hash=composed.lineage_hash,
    )
    return composed, receipt


def _debt_score(debt: EpistemicDebt) -> float:
    return debt.score


def gauss_ceres_reconstruction(profile: SageProfile | None = None) -> DiscoveryPath:
    """Deterministic software reconstruction fixture for the 1801 Ceres target.

    This is not asserted to be Gauss's unique or documented cognitive path.
    It exists to test the Discovery Path IR against a historically anchored
    target already present in the R0.1 seed.
    """
    profile = profile or get_profile("gauss")
    target = discovery_by_id(profile, "gauss_1801_ceres")
    gate_year = target.year - 1
    snapshot = time_machine_snapshot(profile, default_context(profile, gate_year))
    visible = causal_leakage_firewall(profile, target.discovery_id, year=gate_year).visible_discovery_ids
    debt = epistemic_debt_for_discovery(profile, target.discovery_id)

    s0 = EpistemicState(
        "ceres_s0",
        gate_year,
        tuple(sorted(visible)),
        ("historical_problem_statement",),
        snapshot.allowed_atom_ids,
        (target.discovery_id,),
        uncertainty=0.9,
        epistemic_debt=_debt_score(debt),
        provenance_ids=target.source_ids,
    )
    s1 = EpistemicState(
        "ceres_s1",
        gate_year,
        tuple(sorted(visible)),
        ("latent_model", "inverse_problem"),
        snapshot.allowed_atom_ids,
        (target.discovery_id,),
        uncertainty=0.72,
        epistemic_debt=_debt_score(debt),
        provenance_ids=target.source_ids,
    )
    s2 = EpistemicState(
        "ceres_s2",
        target.year,
        tuple(sorted(visible)),
        ("latent_model", "residual_space"),
        snapshot.allowed_atom_ids,
        (target.discovery_id,),
        uncertainty=0.48,
        epistemic_debt=_debt_score(debt),
        provenance_ids=target.source_ids,
    )
    s3 = EpistemicState(
        "ceres_s3",
        target.year,
        tuple(sorted((*visible, target.discovery_id))),
        ("orbit_reconstruction", "residual_space"),
        snapshot.allowed_atom_ids,
        (),
        uncertainty=0.30,
        epistemic_debt=max(0.0, _debt_score(debt) - 0.5),
        provenance_ids=target.source_ids,
    )

    step1 = PathStep(
        "ceres_p1",
        "representation_switch",
        s0.state_id,
        s1.state_id,
        gate_year,
        s0.representation_ids,
        s1.representation_ids,
        evidence_ids=snapshot.allowed_atom_ids,
        cost=ResourceCost(compute=0.2, conceptual=0.9, evidence=0.4, uncertainty=0.4, epistemic_debt=0.2, representation_loss=0.1),
        residuals=ResidualVector(logical=0.2, empirical=0.5, representation=0.2, provenance=0.3, uncertainty=0.5),
        uncertainty_before=s0.uncertainty,
        uncertainty_after=s1.uncertainty,
        note="Reconstruction: reframe the sparse-observation problem as latent-model inference.",
    )
    step2 = PathStep(
        "ceres_p2",
        "approximation_residual",
        s1.state_id,
        s2.state_id,
        target.year,
        s1.representation_ids,
        s2.representation_ids,
        evidence_ids=snapshot.allowed_atom_ids,
        cost=ResourceCost(compute=0.8, conceptual=0.6, evidence=0.5, uncertainty=0.3, epistemic_debt=0.2, risk=0.1),
        residuals=ResidualVector(logical=0.15, empirical=0.25, representation=0.15, provenance=0.3, uncertainty=0.3),
        uncertainty_before=s1.uncertainty,
        uncertainty_after=s2.uncertainty,
        note="Reconstruction: fit candidate latent states and inspect residual structure.",
    )
    step3 = PathStep(
        "ceres_p3",
        "invariant_search",
        s2.state_id,
        s3.state_id,
        target.year,
        s2.representation_ids,
        s3.representation_ids,
        evidence_ids=snapshot.allowed_atom_ids,
        produced_claim_ids=(target.discovery_id,),
        cost=ResourceCost(compute=0.5, conceptual=0.8, evidence=0.4, uncertainty=0.2, epistemic_debt=0.15),
        residuals=ResidualVector(logical=0.1, empirical=0.2, representation=0.1, provenance=0.25, uncertainty=0.2),
        uncertainty_before=s2.uncertainty,
        uncertainty_after=s3.uncertainty,
        note="Reconstruction: retain a candidate orbit whose structure survives residual checks.",
    )
    return DiscoveryPath(
        path_id="gauss_ceres_reconstruction_r04",
        sage_id=profile.sage_id,
        target_discovery_id=target.discovery_id,
        claim_class=ClaimClass.RECONSTRUCTION,
        states=(s0, s1, s2, s3),
        steps=(step1, step2, step3),
        source_ids=target.source_ids,
        counterfactual=False,
    )


def counter_path_fixture(path: DiscoveryPath) -> DiscoveryPath:
    """Build a deterministic adversarial variant for path-difference testing."""
    registry = operator_registry(get_profile(path.sage_id))
    anti = registry["anti_switch_stay_native"]
    s0, _, s2, s3 = path.states
    s1 = EpistemicState(
        "ceres_counter_s1",
        s0.year,
        s0.knowledge_ids,
        ("historical_problem_statement", "native_representation"),
        s0.evidence_ids,
        s0.open_problem_ids,
        uncertainty=0.78,
        epistemic_debt=s0.epistemic_debt,
        provenance_ids=s0.provenance_ids,
    )
    p1 = PathStep(
        "ceres_counter_p1",
        anti.operator_id,
        s0.state_id,
        s1.state_id,
        s0.year,
        s0.representation_ids,
        s1.representation_ids,
        evidence_ids=s0.evidence_ids,
        cost=ResourceCost(compute=0.15, conceptual=0.6, evidence=0.4, uncertainty=0.45, epistemic_debt=0.2),
        residuals=ResidualVector(logical=0.25, empirical=0.5, representation=0.1, provenance=0.3, uncertainty=0.45),
        uncertainty_before=s0.uncertainty,
        uncertainty_after=s1.uncertainty,
        note="Adversarial branch: stay in the native representation before switching.",
    )
    p2 = PathStep(
        "ceres_counter_p2",
        "approximation_residual",
        s1.state_id,
        s2.state_id,
        s2.year,
        s1.representation_ids,
        s2.representation_ids,
        evidence_ids=s1.evidence_ids,
        cost=ResourceCost(compute=0.9, conceptual=0.7, evidence=0.5, uncertainty=0.35, epistemic_debt=0.2, risk=0.1),
        residuals=ResidualVector(logical=0.2, empirical=0.3, representation=0.2, provenance=0.3, uncertainty=0.35),
        uncertainty_before=s1.uncertainty,
        uncertainty_after=s2.uncertainty,
    )
    p3 = PathStep(
        "ceres_counter_p3",
        "invariant_search",
        s2.state_id,
        s3.state_id,
        s3.year,
        s2.representation_ids,
        s3.representation_ids,
        evidence_ids=s2.evidence_ids,
        produced_claim_ids=(path.target_discovery_id,),
        cost=ResourceCost(compute=0.55, conceptual=0.85, evidence=0.4, uncertainty=0.25, epistemic_debt=0.15),
        residuals=ResidualVector(logical=0.12, empirical=0.22, representation=0.12, provenance=0.25, uncertainty=0.22),
        uncertainty_before=s2.uncertainty,
        uncertainty_after=s3.uncertainty,
    )
    return DiscoveryPath(
        path_id="gauss_ceres_counterpath_r04",
        sage_id=path.sage_id,
        target_discovery_id=path.target_discovery_id,
        claim_class=ClaimClass.RECONSTRUCTION,
        states=(s0, s1, s2, s3),
        steps=(p1, p2, p3),
        source_ids=path.source_ids,
    )


def compile_report(profile: SageProfile) -> dict[str, object]:
    path = gauss_ceres_reconstruction(profile)
    audit = audit_path(profile, path)
    counter = counter_path_fixture(path)
    counter_audit = audit_path(profile, counter)
    diff = compare_paths(path, counter)
    return {
        "engine": "Ω-DISCOVERY-PATH-COMPILER-T∞",
        "release": "R0.4",
        "path": asdict(path),
        "audit": asdict(audit),
        "counter_path_audit": asdict(counter_audit),
        "path_diff": asdict(diff),
        "lineage_hash": path.lineage_hash,
        "path_is_historical_causation_claim": False,
        "historical_truth_certified": False,
        "operator_effectiveness_causally_proven": False,
        "oak_note": "The path is an auditable reconstruction model; operator success requires independent comparative evidence.",
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Discovery Path IR R0.4")
    parser.add_argument("--sage", default="gauss")
    args = parser.parse_args(argv)
    profile = get_profile(args.sage)
    print(json.dumps(_jsonable(compile_report(profile)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
