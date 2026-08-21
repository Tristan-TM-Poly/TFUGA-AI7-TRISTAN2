"""Bounded meta-morphogenesis primitives for Ω Generative Closure R0.3.

This module composes existing Generative Closure and MetaScience contracts. It
does not define another Cognitive ISA, Research ABI, representation market, or
epistemic status system.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from omega_meta_science_t.discovery import (
    ArbitrageDecision,
    RepresentationRoute,
    representation_arbitrage,
)
from omega_meta_science_t.geometry import (
    TransformCertificate,
    TransformCertificateReport,
    validate_transform_certificate,
)

from .closure import compute_closure
from .core import Rule


@dataclass(frozen=True)
class ResidualField:
    required: frozenset[str]
    reachable: frozenset[str]
    missing: frozenset[str]
    blocked_rules: tuple[tuple[str, tuple[str, ...]], ...]
    unproduced: frozenset[str]

    @property
    def pressure(self) -> int:
        return len(self.missing)


def compile_residual_field(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    required: Iterable[str],
) -> ResidualField:
    ordered_rules = tuple(rules)
    required_set = frozenset(required)
    closure = compute_closure(seeds, ordered_rules)
    missing = required_set.difference(closure.reachable)
    blocked: list[tuple[str, tuple[str, ...]]] = []
    produced_missing: set[str] = set()
    for rule in ordered_rules:
        if rule.produces & missing:
            produced_missing.update(rule.produces & missing)
            absent = tuple(sorted(rule.requires.difference(closure.reachable)))
            if absent:
                blocked.append((rule.name, absent))
    return ResidualField(
        required=required_set,
        reachable=closure.reachable,
        missing=frozenset(missing),
        blocked_rules=tuple(sorted(blocked)),
        unproduced=frozenset(missing.difference(produced_missing)),
    )


@dataclass(frozen=True)
class GeneratingBasisReport:
    original_seeds: frozenset[str]
    basis: frozenset[str]
    target: frozenset[str]
    reachable: frozenset[str]
    compression_ratio: float
    searched_subsets: int
    exact_within_declared_space: bool = True
    oak_boundary: str = (
        "cardinality-minimal only within the declared finite seed universe and rule system"
    )


def minimal_generating_basis(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    *,
    required: Iterable[str] | None = None,
    max_candidates: int = 16,
) -> GeneratingBasisReport:
    seed_set = frozenset(str(seed) for seed in seeds)
    ordered_rules = tuple(rules)
    if len(seed_set) > max_candidates:
        raise ValueError(
            f"declared seed universe has {len(seed_set)} candidates; max_candidates={max_candidates}"
        )
    full = compute_closure(seed_set, ordered_rules)
    target = full.reachable if required is None else frozenset(required)
    if not target <= full.reachable:
        missing = ",".join(sorted(target.difference(full.reachable)))
        raise ValueError(f"target is not reachable from declared seeds: {missing}")

    ordered_seeds = tuple(sorted(seed_set))
    searched = 0
    for size in range(len(ordered_seeds) + 1):
        for subset in combinations(ordered_seeds, size):
            searched += 1
            candidate = compute_closure(subset, ordered_rules)
            if target <= candidate.reachable:
                ratio = 0.0 if not seed_set else 1.0 - (len(subset) / len(seed_set))
                return GeneratingBasisReport(
                    original_seeds=seed_set,
                    basis=frozenset(subset),
                    target=frozenset(target),
                    reachable=candidate.reachable,
                    compression_ratio=ratio,
                    searched_subsets=searched,
                )
    raise RuntimeError("reachable target had no generating basis in its own finite seed universe")


@dataclass(frozen=True)
class RenormalizationReceipt:
    original_seeds: frozenset[str]
    reduced_seeds: frozenset[str]
    observables: frozenset[str]
    reachable_before: frozenset[str]
    reachable_after: frozenset[str]
    lost_observables: frozenset[str]
    compression_ratio: float
    stable_under_second_pass: bool
    oak_boundary: str = (
        "finite idempotence under this declared reduction operator; not a universal RG fixed point"
    )


def renormalize_seed_set(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    *,
    observables: Iterable[str] | None = None,
    max_candidates: int = 16,
) -> RenormalizationReceipt:
    seed_set = frozenset(seeds)
    ordered_rules = tuple(rules)
    before = compute_closure(seed_set, ordered_rules)
    target = before.reachable if observables is None else frozenset(observables)
    first = minimal_generating_basis(
        seed_set,
        ordered_rules,
        required=target,
        max_candidates=max_candidates,
    )
    after = compute_closure(first.basis, ordered_rules)
    second = minimal_generating_basis(
        first.basis,
        ordered_rules,
        required=target,
        max_candidates=max_candidates,
    )
    return RenormalizationReceipt(
        original_seeds=seed_set,
        reduced_seeds=first.basis,
        observables=frozenset(target),
        reachable_before=before.reachable,
        reachable_after=after.reachable,
        lost_observables=frozenset(target.difference(after.reachable)),
        compression_ratio=first.compression_ratio,
        stable_under_second_pass=second.basis == first.basis,
    )


@dataclass(frozen=True)
class MorphogenesisReceipt:
    operator: str
    source_id: str
    target_id: str
    transform: TransformCertificateReport
    representation: ArbitrageDecision | None
    assumptions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    residuals: tuple[str, ...]
    uncertainty: float
    cost: float
    risk: float
    rollback: str
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS certifies declared structural receipt constraints only; it is not proof of improvement or truth"
    )


def compile_morphogenesis_receipt(
    *,
    operator: str,
    source_id: str,
    target_id: str,
    invariants_before: Sequence[str],
    invariants_after: Sequence[str],
    roundtrip_error: float,
    max_roundtrip_error: float,
    domain: str,
    provenance: str,
    assumptions: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
    residuals: Sequence[str] = (),
    uncertainty: float = 0.0,
    cost: float = 0.0,
    risk: float = 0.0,
    rollback: str = "",
    representation_routes: Sequence[RepresentationRoute] = (),
    max_roundtrip_loss: float = 0.05,
    min_invariant_retention: float = 0.95,
) -> MorphogenesisReceipt:
    certificate = TransformCertificate(
        transform_id=str(operator),
        source_id=str(source_id),
        target_id=str(target_id),
        invariants_before=tuple(invariants_before),
        invariants_after=tuple(invariants_after),
        roundtrip_error=float(roundtrip_error),
        max_roundtrip_error=float(max_roundtrip_error),
        domain=str(domain),
        provenance=str(provenance),
    )
    transform_report = validate_transform_certificate(certificate)

    blockers = list(transform_report.blockers)
    if not str(operator).strip():
        blockers.append("missing_operator")
    if not evidence_refs:
        blockers.append("missing_evidence_refs")
    if not 0.0 <= float(uncertainty) <= 1.0:
        blockers.append("uncertainty_out_of_range")
    if float(cost) < 0.0:
        blockers.append("negative_cost")
    if float(risk) < 0.0:
        blockers.append("negative_risk")
    if not str(rollback).strip():
        blockers.append("missing_rollback")

    representation: ArbitrageDecision | None = None
    if representation_routes:
        try:
            representation = representation_arbitrage(
                tuple(representation_routes),
                max_roundtrip_loss=max_roundtrip_loss,
                min_invariant_retention=min_invariant_retention,
            )
        except ValueError:
            blockers.append("no_representation_route_passes_fidelity_gates")

    blockers = sorted(set(blockers))
    return MorphogenesisReceipt(
        operator=str(operator),
        source_id=str(source_id),
        target_id=str(target_id),
        transform=transform_report,
        representation=representation,
        assumptions=tuple(assumptions),
        evidence_refs=tuple(evidence_refs),
        residuals=tuple(residuals),
        uncertainty=float(uncertainty),
        cost=float(cost),
        risk=float(risk),
        rollback=str(rollback),
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(blockers),
    )
