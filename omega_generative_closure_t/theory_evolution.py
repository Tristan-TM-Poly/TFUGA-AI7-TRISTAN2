"""Ω Theory Evolution R0.4: bounded regeneration benchmark and selection court.

This module is intentionally small. It reuses R0.3 Generative Closure primitives
and the existing Pareto semantics. It does not claim that a structural closure
benchmark proves scientific truth, and it never fabricates a winner from a tie.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .closure import compute_closure
from .core import MaxMinVector, Rule
from .maxmin import pareto_frontier
from .morphogenesis import minimal_generating_basis, renormalize_seed_set


@dataclass(frozen=True)
class AblationResult:
    removed_seed: str
    retained_observables: frozenset[str]
    lost_observables: frozenset[str]


@dataclass(frozen=True)
class RegenerationBenchmarkReport:
    original_seeds: frozenset[str]
    reduced_seeds: frozenset[str]
    observables: frozenset[str]
    reachable_before: frozenset[str]
    reachable_after: frozenset[str]
    compression_ratio: float
    retained_observables_ratio: float
    closure_reconstruction_ratio: float
    searched_subsets: int
    fired_rule_cost: float
    evidence_debt: float
    ablations: tuple[AblationResult, ...]
    stable_under_second_pass: bool
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means declared finite structural observables were regenerated under the supplied rule system; "
        "it is not scientific validation, semantic equivalence, or proof of global minimality"
    )


def _safe_ratio(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else numerator / denominator


def regeneration_benchmark(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    *,
    observables: Iterable[str] | None = None,
    max_candidates: int = 16,
    min_rule_evidence: float = 0.0,
) -> RegenerationBenchmarkReport:
    """Compare full, reduced and counterfactual-ablation closures.

    The basis search is exact only inside the declared finite seed universe.
    Evidence debt is a bookkeeping signal over fired rules, not a probability.
    """

    seed_set = frozenset(str(seed) for seed in seeds)
    ordered_rules = tuple(rules)
    before = compute_closure(seed_set, ordered_rules)
    target = before.reachable if observables is None else frozenset(str(x) for x in observables)

    basis = minimal_generating_basis(
        seed_set,
        ordered_rules,
        required=target,
        max_candidates=max_candidates,
    )
    renorm = renormalize_seed_set(
        seed_set,
        ordered_rules,
        observables=target,
        max_candidates=max_candidates,
    )
    after = compute_closure(basis.basis, ordered_rules)

    retained = frozenset(target & after.reachable)
    retained_ratio = _safe_ratio(len(retained), len(target))
    reconstruction_ratio = _safe_ratio(len(after.reachable), len(before.reachable))

    rule_by_name = {rule.name: rule for rule in ordered_rules}
    fired = tuple(rule_by_name[name] for name in after.fired_rules if name in rule_by_name)
    fired_rule_cost = sum(max(0.0, float(rule.cost)) for rule in fired)
    evidence_debt = sum(max(0.0, float(min_rule_evidence) - float(rule.evidence)) for rule in fired)

    ablations: list[AblationResult] = []
    for seed in sorted(basis.basis):
        counterfactual = compute_closure(basis.basis.difference({seed}), ordered_rules)
        retained_cf = frozenset(target & counterfactual.reachable)
        ablations.append(
            AblationResult(
                removed_seed=seed,
                retained_observables=retained_cf,
                lost_observables=frozenset(target.difference(counterfactual.reachable)),
            )
        )

    blockers: list[str] = []
    if retained != target:
        blockers.append("lost_declared_observables")
    if not renorm.stable_under_second_pass:
        blockers.append("second_pass_instability")
    if evidence_debt > 0.0:
        blockers.append("fired_rule_evidence_below_declared_floor")

    return RegenerationBenchmarkReport(
        original_seeds=seed_set,
        reduced_seeds=basis.basis,
        observables=frozenset(target),
        reachable_before=before.reachable,
        reachable_after=after.reachable,
        compression_ratio=basis.compression_ratio,
        retained_observables_ratio=retained_ratio,
        closure_reconstruction_ratio=reconstruction_ratio,
        searched_subsets=basis.searched_subsets,
        fired_rule_cost=fired_rule_cost,
        evidence_debt=evidence_debt,
        ablations=tuple(ablations),
        stable_under_second_pass=renorm.stable_under_second_pass,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class NextTransformationDecision:
    decision: str
    pareto_frontier: tuple[str, ...]
    oak_status: str
    reasons: tuple[str, ...]
    oak_boundary: str = (
        "selection is relative to declared MaxMinVector axes; a unique Pareto survivor is not proof of real-world superiority"
    )


def select_next_transformation(
    candidates: Mapping[str, MaxMinVector],
) -> NextTransformationDecision:
    """Select only when Pareto dominance yields one survivor; ties remain HOLD.

    Empty candidate sets make IDENTITY/DO NOTHING a first-class outcome.
    No scalar score is used to manufacture a winner.
    """

    normalized = {str(name): vector for name, vector in candidates.items()}
    if not normalized:
        return NextTransformationDecision(
            decision="IDENTITY",
            pareto_frontier=(),
            oak_status="PASS",
            reasons=("no_candidate_transformations", "do_nothing_is_first_class"),
        )

    frontier = pareto_frontier(normalized)
    if len(frontier) == 1:
        return NextTransformationDecision(
            decision=frontier[0],
            pareto_frontier=frontier,
            oak_status="PASS",
            reasons=("unique_pareto_survivor",),
        )

    return NextTransformationDecision(
        decision="HOLD",
        pareto_frontier=frontier,
        oak_status="HOLD",
        reasons=("pareto_tie_or_incomparability", "additional_discriminating_evidence_required"),
    )


@dataclass(frozen=True)
class PowerLadderStep:
    n: int
    current_capacity: int
    probe_n: int
    probe_capacity: int


def power_ladder_step(n: int) -> PowerLadderStep:
    """Encode the 2^n -> n+1 falsification probe used by the artifact workflow."""

    if n < 0:
        raise ValueError("n must be non-negative")
    return PowerLadderStep(
        n=n,
        current_capacity=2**n,
        probe_n=n + 1,
        probe_capacity=2 ** (n + 1),
    )
