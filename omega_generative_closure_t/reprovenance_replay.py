"""Ω Meta-Theory R0.10: independent slices, provenance leakage, and replay gates.

R0.10 attacks cross-run self-consistency and hidden evidence coupling before any
further meta-layer is allowed. Independence here is identity/provenance-level
and finite; it is not statistical or causal independence.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping


@dataclass(frozen=True)
class FrozenSlice:
    name: str
    provenance_ids: frozenset[str]
    benchmark_ids: frozenset[str]

    @classmethod
    def make(
        cls,
        name: str,
        provenance_ids: Iterable[str],
        benchmark_ids: Iterable[str] = (),
    ) -> "FrozenSlice":
        return cls(
            str(name),
            frozenset(str(x) for x in provenance_ids),
            frozenset(str(x) for x in benchmark_ids),
        )


@dataclass(frozen=True)
class ProvenanceIndependenceReport:
    slice_count: int
    shared_provenance_pairs: tuple[tuple[str, str, tuple[str, ...]], ...]
    benchmark_leakage: tuple[tuple[str, tuple[str, ...]], ...]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PASS means no declared provenance identity overlap or benchmark/training identity leakage was found; "
        "it is not proof of statistical, semantic, organizational, or causal independence"
    )


def provenance_independence(
    slices: Iterable[FrozenSlice],
    *,
    training_provenance_ids: Iterable[str] = (),
    require_pairwise_disjoint: bool = True,
) -> ProvenanceIndependenceReport:
    items = tuple(slices)
    training = frozenset(str(x) for x in training_provenance_ids)
    shared: list[tuple[str, str, tuple[str, ...]]] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            overlap = tuple(sorted(left.provenance_ids & right.provenance_ids))
            if overlap:
                shared.append((left.name, right.name, overlap))
    leakage: list[tuple[str, tuple[str, ...]]] = []
    for item in items:
        leaked = tuple(sorted(item.benchmark_ids & training))
        if leaked:
            leakage.append((item.name, leaked))

    blockers: list[str] = []
    if len(items) < 2:
        blockers.append("insufficient_frozen_slices")
    if require_pairwise_disjoint and shared:
        blockers.append("shared_provenance_detected")
    if leakage:
        blockers.append("benchmark_training_leakage_detected")
    return ProvenanceIndependenceReport(
        slice_count=len(items),
        shared_provenance_pairs=tuple(shared),
        benchmark_leakage=tuple(leakage),
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class CrossRunReproducibilityReport:
    run_count: int
    common_case_count: int
    agreement_ratio: float
    disagreements: tuple[str, ...]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "reproducibility is exact decision agreement on common frozen case identifiers; "
        "agreement does not imply correctness, truth, or external validity"
    )


def cross_run_reproducibility(
    runs: Mapping[str, Mapping[str, str]],
    *,
    min_runs: int = 2,
    min_agreement_ratio: float = 1.0,
) -> CrossRunReproducibilityReport:
    if min_runs < 2:
        raise ValueError("min_runs must be >= 2")
    if not 0.0 <= float(min_agreement_ratio) <= 1.0:
        raise ValueError("min_agreement_ratio must be in [0, 1]")
    normalized = {
        str(run): {str(case): str(decision) for case, decision in decisions.items()}
        for run, decisions in runs.items()
    }
    blockers: list[str] = []
    if len(normalized) < min_runs:
        blockers.append("insufficient_independent_runs")
    common = set.intersection(*(set(values) for values in normalized.values())) if normalized else set()
    if not common:
        blockers.append("no_common_frozen_cases")
    disagreements: list[str] = []
    for case in sorted(common):
        verdicts = {values[case] for values in normalized.values()}
        if len(verdicts) != 1:
            disagreements.append(case)
    ratio = 0.0 if not common else (len(common) - len(disagreements)) / len(common)
    if common and ratio < min_agreement_ratio:
        blockers.append("cross_run_decision_instability")
    return CrossRunReproducibilityReport(
        run_count=len(normalized),
        common_case_count=len(common),
        agreement_ratio=ratio,
        disagreements=tuple(disagreements),
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class HistoricalReplayReport:
    case_count: int
    preserved_count: int
    regression_count: int
    changed_cases: tuple[str, ...]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "historical replay compares supplied frozen expected decisions with supplied candidate-policy decisions; "
        "preservation is not proof the historical decisions were optimal"
    )


def historical_replay(
    expected: Mapping[str, str],
    candidate: Mapping[str, str],
    *,
    allowed_changes: Iterable[str] = (),
) -> HistoricalReplayReport:
    allowed = frozenset(str(x) for x in allowed_changes)
    common = sorted(set(expected) & set(candidate))
    changed = tuple(case for case in common if str(expected[case]) != str(candidate[case]))
    regressions = tuple(case for case in changed if case not in allowed)
    blockers: list[str] = []
    if not common:
        blockers.append("no_historical_replay_cases")
    if regressions:
        blockers.append("unapproved_historical_decision_regression")
    return HistoricalReplayReport(
        case_count=len(common),
        preserved_count=len(common) - len(changed),
        regression_count=len(regressions),
        changed_cases=changed,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class CounterfactualReplayReport:
    case_count: int
    wins: int
    ties: int
    losses: int
    mean_delta: float
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "counterfactual replay compares supplied finite utility traces under a frozen utility definition; "
        "positive replay does not establish real-world causal benefit"
    )


def counterfactual_replay(
    observations: Iterable[tuple[float, float]],
    *,
    allow_losses: int = 0,
    min_mean_delta: float = 0.0,
) -> CounterfactualReplayReport:
    if allow_losses < 0:
        raise ValueError("allow_losses must be >= 0")
    pairs = tuple((float(base), float(candidate)) for base, candidate in observations)
    if any(not isfinite(base) or not isfinite(candidate) for base, candidate in pairs):
        raise ValueError("counterfactual observations must be finite")
    deltas = tuple(candidate - base for base, candidate in pairs)
    wins = sum(delta > 0.0 for delta in deltas)
    ties = sum(delta == 0.0 for delta in deltas)
    losses = sum(delta < 0.0 for delta in deltas)
    mean_delta = 0.0 if not deltas else sum(deltas) / len(deltas)
    blockers: list[str] = []
    if not pairs:
        blockers.append("missing_counterfactual_replay_cases")
    if losses > allow_losses:
        blockers.append("counterfactual_regression_budget_exceeded")
    if pairs and mean_delta < min_mean_delta:
        blockers.append("counterfactual_mean_gain_below_threshold")
    return CounterfactualReplayReport(
        len(pairs), wins, ties, losses, mean_delta,
        "PASS" if not blockers else "HOLD",
        tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class R10PromotionGate:
    provenance: ProvenanceIndependenceReport
    reproducibility: CrossRunReproducibilityReport
    historical: HistoricalReplayReport
    counterfactual: CounterfactualReplayReport
    decision: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PROMOTE means all supplied finite R0.10 courts passed; it is not universal truth or authority to bypass external gates"
    )


def r10_promotion_gate(
    provenance: ProvenanceIndependenceReport,
    reproducibility: CrossRunReproducibilityReport,
    historical: HistoricalReplayReport,
    counterfactual: CounterfactualReplayReport,
) -> R10PromotionGate:
    blockers = []
    for prefix, report in (
        ("provenance", provenance),
        ("reproducibility", reproducibility),
        ("historical", historical),
        ("counterfactual", counterfactual),
    ):
        if report.oak_status != "PASS":
            blockers.extend(f"{prefix}:{item}" for item in report.blockers)
    return R10PromotionGate(
        provenance,
        reproducibility,
        historical,
        counterfactual,
        "PROMOTE" if not blockers else "HOLD",
        tuple(blockers),
    )
