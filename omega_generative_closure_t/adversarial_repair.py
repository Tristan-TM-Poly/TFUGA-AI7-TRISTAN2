"""Ω Meta-Theory R0.6: adversarial probes and minimal counterexample repair.

R0.6 turns R0.5 transfer failures into explicit challenge probes and searches
for the smallest additive repair inside a declared finite candidate seed pool.
No repair is promoted as globally optimal or scientifically true.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from .closure import compute_closure
from .core import Rule
from .cross_context import CrossContextRegenerationReport, ProbeFamily


@dataclass(frozen=True)
class AdversarialProbe:
    name: str
    observables: frozenset[str]
    source_families: tuple[str, ...]
    oak_boundary: str = (
        "probe is synthesized from observed transfer residuals; it is not an independent proof of completeness"
    )


def synthesize_adversarial_probe(
    report: CrossContextRegenerationReport,
    *,
    name: str = "adversarial_residual_union",
) -> AdversarialProbe:
    failing = tuple(result for result in report.family_results if result.missing)
    observables = frozenset().union(*(result.missing for result in failing)) if failing else frozenset()
    return AdversarialProbe(
        name=str(name),
        observables=observables,
        source_families=tuple(sorted(result.family for result in failing)),
    )


@dataclass(frozen=True)
class RepairEvaluation:
    family: str
    retained_ratio: float
    missing: frozenset[str]


@dataclass(frozen=True)
class MinimalRepairReport:
    original_basis: frozenset[str]
    repaired_basis: frozenset[str]
    added_seeds: frozenset[str]
    evaluations: tuple[RepairEvaluation, ...]
    searched_subsets: int
    min_retained_ratio: float
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "minimal means minimum added-seed cardinality only within the declared finite candidate pool and supplied probe families"
    )


def _evaluate_basis(
    basis: frozenset[str],
    rules: tuple[Rule, ...],
    families: tuple[ProbeFamily, ...],
) -> tuple[RepairEvaluation, ...]:
    closure = compute_closure(basis, rules)
    results: list[RepairEvaluation] = []
    for family in families:
        retained = family.observables & closure.reachable
        missing = frozenset(family.observables.difference(closure.reachable))
        ratio = 1.0 if not family.observables else len(retained) / len(family.observables)
        results.append(RepairEvaluation(family.name, ratio, missing))
    return tuple(results)


def minimal_counterexample_repair(
    basis: Iterable[str],
    candidate_seeds: Iterable[str],
    rules: Iterable[Rule],
    probe_families: Iterable[ProbeFamily],
    *,
    min_transfer_ratio: float = 1.0,
    max_candidates: int = 16,
) -> MinimalRepairReport:
    """Find the smallest additive seed repair that satisfies declared probes.

    Existing basis elements are preserved. Search is exhaustive only over the
    declared finite candidate additions and therefore bounded by max_candidates.
    """

    if not 0.0 <= float(min_transfer_ratio) <= 1.0:
        raise ValueError("min_transfer_ratio must be in [0, 1]")

    original = frozenset(str(x) for x in basis)
    pool = frozenset(str(x) for x in candidate_seeds).difference(original)
    if len(pool) > max_candidates:
        raise ValueError(
            f"declared repair pool has {len(pool)} candidates; max_candidates={max_candidates}"
        )
    families = tuple(probe_families)
    if not families:
        raise ValueError("at least one probe family is required")
    ordered_rules = tuple(rules)
    ordered_pool = tuple(sorted(pool))

    searched = 0
    for size in range(len(ordered_pool) + 1):
        for additions in combinations(ordered_pool, size):
            searched += 1
            repaired = original | frozenset(additions)
            evaluations = _evaluate_basis(repaired, ordered_rules, families)
            if all(item.retained_ratio >= min_transfer_ratio for item in evaluations):
                return MinimalRepairReport(
                    original_basis=original,
                    repaired_basis=repaired,
                    added_seeds=frozenset(additions),
                    evaluations=evaluations,
                    searched_subsets=searched,
                    min_retained_ratio=min(item.retained_ratio for item in evaluations),
                    oak_status="PASS",
                    blockers=(),
                )

    evaluations = _evaluate_basis(original, ordered_rules, families)
    return MinimalRepairReport(
        original_basis=original,
        repaired_basis=original,
        added_seeds=frozenset(),
        evaluations=evaluations,
        searched_subsets=searched,
        min_retained_ratio=min(item.retained_ratio for item in evaluations),
        oak_status="HOLD",
        blockers=("no_declared_repair_satisfies_probe_families",),
    )


@dataclass(frozen=True)
class RepairCycleReport:
    adversarial_probe: AdversarialProbe
    repair: MinimalRepairReport
    regression_preserved: bool
    oak_status: str
    blockers: tuple[str, ...]


def counterexample_repair_cycle(
    cross_context_report: CrossContextRegenerationReport,
    candidate_seeds: Iterable[str],
    rules: Iterable[Rule],
    probe_families: Iterable[ProbeFamily],
    *,
    min_transfer_ratio: float = 1.0,
    max_candidates: int = 16,
) -> RepairCycleReport:
    """Synthesize a residual probe, repair minimally, and preserve old basis."""

    probe = synthesize_adversarial_probe(cross_context_report)
    repair = minimal_counterexample_repair(
        cross_context_report.training_basis,
        candidate_seeds,
        rules,
        probe_families,
        min_transfer_ratio=min_transfer_ratio,
        max_candidates=max_candidates,
    )
    regression_preserved = cross_context_report.training_basis <= repair.repaired_basis
    blockers = list(repair.blockers)
    if not probe.observables and cross_context_report.transfer_failures:
        blockers.append("transfer_failure_without_explicit_missing_observables")
    if not regression_preserved:
        blockers.append("original_basis_not_preserved")
    return RepairCycleReport(
        adversarial_probe=probe,
        repair=repair,
        regression_preserved=regression_preserved,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )
