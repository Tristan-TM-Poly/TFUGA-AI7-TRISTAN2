"""Matched-cohort and sequential decision court for Capability OS.

This module consumes already-collected ProspectiveExecutionReceipt objects.
It does not fabricate future observations and it does not turn matching into
causal identification. Matching is exact over caller-declared strata only.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable, Mapping

from omega_capability_os_t.prospective_measurement import (
    FrozenMeasurementCriteria,
    ProspectiveExecutionReceipt,
)


@dataclass(frozen=True)
class MatchedExecution:
    receipt: ProspectiveExecutionReceipt
    strata: Mapping[str, str]


@dataclass(frozen=True)
class SequentialCriteria:
    min_pairs: int = 3
    max_pairs: int = 20
    z_value: float = 1.96
    noninferiority_margin: float = 0.0
    require_strict_improvement: bool = True

    def __post_init__(self) -> None:
        if self.min_pairs < 1 or self.max_pairs < self.min_pairs:
            raise ValueError("require 1 <= min_pairs <= max_pairs")
        if not isfinite(self.z_value) or self.z_value <= 0:
            raise ValueError("z_value must be finite and > 0")
        if not isfinite(self.noninferiority_margin) or self.noninferiority_margin < 0:
            raise ValueError("noninferiority_margin must be finite and >= 0")


@dataclass(frozen=True)
class MetricEffect:
    metric: str
    pair_count: int
    mean_delta: float
    standard_error: float
    lower_bound: float
    upper_bound: float
    standardized_effect: float | None


@dataclass(frozen=True)
class MatchedCohortReport:
    pair_count: int
    unmatched_baseline: int
    unmatched_transplant: int
    effects: tuple[MetricEffect, ...]
    decision: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "PROMOTE means the supplied exact-matched finite pairs satisfy the frozen sequential court under a normal-approximation interval. "
        "Exact matching does not prove matched difficulty; the interval is not a causal confidence guarantee; finite non-inferiority is not universal improvement."
    )


def _key(item: MatchedExecution, keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(item.strata.get(k, "")) for k in keys)


def _pair_exact(
    items: tuple[MatchedExecution, ...], keys: tuple[str, ...]
) -> tuple[tuple[MatchedExecution, MatchedExecution], ...]:
    baseline: dict[tuple[str, ...], list[MatchedExecution]] = {}
    transplant: dict[tuple[str, ...], list[MatchedExecution]] = {}
    for item in items:
        bucket = baseline if item.receipt.cohort == "baseline" else transplant
        bucket.setdefault(_key(item, keys), []).append(item)
    pairs: list[tuple[MatchedExecution, MatchedExecution]] = []
    for key in sorted(set(baseline) & set(transplant)):
        bs = sorted(baseline[key], key=lambda x: x.receipt.execution_id)
        ts = sorted(transplant[key], key=lambda x: x.receipt.execution_id)
        pairs.extend(zip(bs[: min(len(bs), len(ts))], ts[: min(len(bs), len(ts))]))
    return tuple(pairs)


def _effect(metric: str, pairs: tuple[tuple[MatchedExecution, MatchedExecution], ...], z: float) -> MetricEffect:
    deltas = [
        float(t.receipt.measurements[metric]) - float(b.receipt.measurements[metric])
        for b, t in pairs
    ]
    n = len(deltas)
    mean = sum(deltas) / n
    if n < 2:
        se = float("inf")
        lo, hi = float("-inf"), float("inf")
        standardized = None
    else:
        variance = sum((x - mean) ** 2 for x in deltas) / (n - 1)
        sd = sqrt(variance)
        se = sd / sqrt(n)
        lo, hi = mean - z * se, mean + z * se
        standardized = None if sd == 0.0 else mean / sd
    return MetricEffect(metric, n, mean, se, lo, hi, standardized)


def compare_matched_cohorts(
    measurement_criteria: FrozenMeasurementCriteria,
    sequential_criteria: SequentialCriteria,
    executions: Iterable[MatchedExecution],
    *,
    match_keys: Iterable[str] = ("task_family", "difficulty_band", "risk_band"),
) -> MatchedCohortReport:
    items = tuple(executions)
    keys = tuple(str(key) for key in match_keys)
    blockers: list[str] = []
    if not keys:
        blockers.append("missing_match_keys")
    if any(not key.strip() for key in keys):
        blockers.append("blank_match_key")
    if len(set(keys)) != len(keys):
        blockers.append("duplicate_match_key")

    expected_digest = measurement_criteria.digest()
    if any(x.receipt.criteria_digest != expected_digest for x in items):
        blockers.append("criteria_digest_mismatch")
    if any(x.receipt.authority_widening for x in items):
        blockers.append("authority_widening_detected")
    if keys and any(any(not str(x.strata.get(k, "")) for k in keys) for x in items):
        blockers.append("missing_match_stratum")
    if any(set(measurement_criteria.metrics) - set(x.receipt.measurements) for x in items):
        blockers.append("missing_frozen_metric")

    pairs = () if blockers else _pair_exact(items, keys)
    baseline_count = sum(x.receipt.cohort == "baseline" for x in items)
    transplant_count = sum(x.receipt.cohort == "transplant" for x in items)
    pair_count = len(pairs)
    unmatched_baseline = baseline_count - pair_count
    unmatched_transplant = transplant_count - pair_count

    effects: tuple[MetricEffect, ...] = ()
    if pair_count:
        effects = tuple(_effect(m, pairs, sequential_criteria.z_value) for m in measurement_criteria.metrics)

    if pair_count < sequential_criteria.min_pairs:
        blockers.append("insufficient_matched_pairs")
        decision = "HOLD"
    else:
        regressed = [e.metric for e in effects if e.upper_bound > sequential_criteria.noninferiority_margin]
        improved = [e.metric for e in effects if e.upper_bound < 0.0]
        if regressed:
            blockers.append("uncertainty_exceeds_noninferiority_margin")
        if sequential_criteria.require_strict_improvement and not improved:
            blockers.append("no_uncertainty_bounded_improvement")
        if not blockers:
            decision = "PROMOTE"
        elif pair_count >= sequential_criteria.max_pairs:
            decision = "STOP"
        else:
            decision = "HOLD"

    return MatchedCohortReport(
        pair_count,
        unmatched_baseline,
        unmatched_transplant,
        effects,
        decision,
        tuple(sorted(set(blockers))),
    )
