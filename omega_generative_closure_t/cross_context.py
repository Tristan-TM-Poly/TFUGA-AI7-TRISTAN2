"""Ω Meta-Theory R0.5: cross-context regeneration and false-fixed-point detection.

A basis that is minimal or stable in one probe family is not automatically
portable to another. Transfer failures are measured as residuals rather than
raised as exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .closure import compute_closure
from .core import Rule
from .theory_evolution import RegenerationBenchmarkReport, regeneration_benchmark


@dataclass(frozen=True)
class ProbeFamily:
    name: str
    observables: frozenset[str]

    @classmethod
    def make(cls, name: str, observables: Iterable[str]) -> "ProbeFamily":
        return cls(name=str(name), observables=frozenset(str(x) for x in observables))


@dataclass(frozen=True)
class ProbeFamilyResult:
    family: str
    observables: frozenset[str]
    reachable: frozenset[str]
    retained: frozenset[str]
    missing: frozenset[str]
    retained_ratio: float


@dataclass(frozen=True)
class CrossContextRegenerationReport:
    training_family: str
    training_report: RegenerationBenchmarkReport
    training_basis: frozenset[str]
    family_results: tuple[ProbeFamilyResult, ...]
    min_retained_ratio: float
    mean_retained_ratio: float
    transfer_failures: tuple[str, ...]
    false_fixed_point: bool
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means the declared basis retained declared observables across the supplied finite probe families; "
        "it is not universal generalization, semantic equivalence, or scientific truth"
    )


def _evaluate_fixed_basis(
    basis: frozenset[str],
    rules: tuple[Rule, ...],
    family: ProbeFamily,
) -> ProbeFamilyResult:
    closure = compute_closure(basis, rules)
    retained = frozenset(family.observables & closure.reachable)
    missing = frozenset(family.observables.difference(closure.reachable))
    ratio = 1.0 if not family.observables else len(retained) / len(family.observables)
    return ProbeFamilyResult(
        family=family.name,
        observables=family.observables,
        reachable=closure.reachable,
        retained=retained,
        missing=missing,
        retained_ratio=ratio,
    )


def cross_context_regeneration(
    seeds: Iterable[str],
    rules: Iterable[Rule],
    probe_families: Iterable[ProbeFamily],
    *,
    training_family: str,
    max_candidates: int = 16,
    min_transfer_ratio: float = 1.0,
    min_rule_evidence: float = 0.0,
) -> CrossContextRegenerationReport:
    families = tuple(probe_families)
    if not families:
        raise ValueError("at least one probe family is required")
    names = [family.name for family in families]
    if len(set(names)) != len(names):
        raise ValueError("probe family names must be unique")
    by_name = {family.name: family for family in families}
    if training_family not in by_name:
        raise ValueError("training_family must name one supplied probe family")
    if not 0.0 <= float(min_transfer_ratio) <= 1.0:
        raise ValueError("min_transfer_ratio must be in [0, 1]")

    ordered_rules = tuple(rules)
    train = regeneration_benchmark(
        seeds,
        ordered_rules,
        observables=by_name[training_family].observables,
        max_candidates=max_candidates,
        min_rule_evidence=min_rule_evidence,
    )
    basis = train.reduced_seeds

    results = tuple(_evaluate_fixed_basis(basis, ordered_rules, family) for family in families)
    ratios = [result.retained_ratio for result in results]
    transfer_failures = tuple(
        sorted(result.family for result in results if result.retained_ratio < min_transfer_ratio)
    )

    local_fixed = train.stable_under_second_pass and train.oak_status == "PASS"
    false_fixed_point = local_fixed and bool(transfer_failures)

    blockers: list[str] = []
    if train.oak_status != "PASS":
        blockers.append("training_family_not_structurally_passed")
    if transfer_failures:
        blockers.append("cross_context_transfer_failure")
    if false_fixed_point:
        blockers.append("false_fixed_point_detected")

    return CrossContextRegenerationReport(
        training_family=training_family,
        training_report=train,
        training_basis=basis,
        family_results=results,
        min_retained_ratio=min(ratios),
        mean_retained_ratio=sum(ratios) / len(ratios),
        transfer_failures=transfer_failures,
        false_fixed_point=false_fixed_point,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class MetricSensitivityReport:
    rankings: tuple[tuple[str, tuple[str, ...]], ...]
    stable_winner: str | None
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "metric agreement is a robustness signal only; disagreement requires HOLD rather than arbitrary scalarization"
    )


def metric_sensitivity(
    metric_rankings: Mapping[str, Iterable[str]],
) -> MetricSensitivityReport:
    if not metric_rankings:
        return MetricSensitivityReport((), None, "HOLD", ("missing_metric_rankings",))

    normalized = tuple(
        sorted((str(metric), tuple(str(x) for x in ranking)) for metric, ranking in metric_rankings.items())
    )
    nonempty = [ranking for _, ranking in normalized if ranking]
    if not nonempty:
        return MetricSensitivityReport(normalized, None, "HOLD", ("all_rankings_empty",))

    winners = {ranking[0] for ranking in nonempty}
    if len(winners) == 1:
        return MetricSensitivityReport(normalized, next(iter(winners)), "PASS", ())

    return MetricSensitivityReport(
        normalized,
        None,
        "HOLD",
        ("metric_sensitive_winner", "additional_discriminating_evidence_required"),
    )
