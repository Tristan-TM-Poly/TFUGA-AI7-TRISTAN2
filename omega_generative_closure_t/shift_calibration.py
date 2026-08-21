"""Ω Meta-Theory R0.9: population shift, proxy calibration, challenge ablation, and adaptive stopping.

R0.9 attacks the assumptions behind R0.8: the candidate population may move,
the discrimination proxy may be miscalibrated, challenge families may be
redundant, and continued challenge generation may no longer justify its cost.
All verdicts are finite and local to supplied populations, criteria, and traces.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from .adversarial_authority import ChallengeAuthority
from .causal_challenge import FrozenEvaluator, evaluate_frozen_challenge
from .core import Rule
from .cross_context import ProbeFamily


@dataclass(frozen=True)
class PopulationShiftReport:
    reference_count: int
    shifted_count: int
    overlap_count: int
    jaccard_overlap: float
    introduced: frozenset[str]
    removed: frozenset[str]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "population overlap is an identity-level finite shift signal; it does not prove distributional equivalence"
    )


def candidate_population_shift(
    reference_ids: Iterable[str],
    shifted_ids: Iterable[str],
    *,
    min_jaccard_overlap: float = 0.5,
) -> PopulationShiftReport:
    if not 0.0 <= float(min_jaccard_overlap) <= 1.0:
        raise ValueError("min_jaccard_overlap must be in [0, 1]")
    reference = frozenset(str(x) for x in reference_ids)
    shifted = frozenset(str(x) for x in shifted_ids)
    union = reference | shifted
    overlap = reference & shifted
    jaccard = 1.0 if not union else len(overlap) / len(union)
    blockers: list[str] = []
    if not reference or not shifted:
        blockers.append("missing_population")
    if jaccard < min_jaccard_overlap:
        blockers.append("candidate_population_shift_exceeds_declared_tolerance")
    return PopulationShiftReport(
        reference_count=len(reference),
        shifted_count=len(shifted),
        overlap_count=len(overlap),
        jaccard_overlap=jaccard,
        introduced=frozenset(shifted - reference),
        removed=frozenset(reference - shifted),
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class ProxyCalibrationReport:
    sample_count: int
    mean_absolute_error: float
    mean_signed_error: float
    max_absolute_error: float
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "calibration compares supplied proxy predictions to supplied realized finite gains; it does not validate the proxy universally"
    )


def calibrate_information_proxy(
    observations: Iterable[tuple[float, float]],
    *,
    min_samples: int = 3,
    max_mean_absolute_error: float = 0.20,
) -> ProxyCalibrationReport:
    if min_samples < 1:
        raise ValueError("min_samples must be >= 1")
    if max_mean_absolute_error < 0.0:
        raise ValueError("max_mean_absolute_error must be >= 0")
    pairs = tuple((float(pred), float(real)) for pred, real in observations)
    if any(not isfinite(pred) or not isfinite(real) for pred, real in pairs):
        raise ValueError("proxy calibration observations must be finite")
    errors = tuple(pred - real for pred, real in pairs)
    abs_errors = tuple(abs(err) for err in errors)
    mae = 0.0 if not abs_errors else sum(abs_errors) / len(abs_errors)
    bias = 0.0 if not errors else sum(errors) / len(errors)
    max_error = 0.0 if not abs_errors else max(abs_errors)
    blockers: list[str] = []
    if len(pairs) < min_samples:
        blockers.append("insufficient_proxy_calibration_samples")
    if pairs and mae > max_mean_absolute_error:
        blockers.append("information_proxy_miscalibrated")
    return ProxyCalibrationReport(
        sample_count=len(pairs),
        mean_absolute_error=mae,
        mean_signed_error=bias,
        max_absolute_error=max_error,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class ChallengeAblation:
    removed_family: str
    distinct_signatures_before: int
    distinct_signatures_after: int
    discriminative_loss: int


@dataclass(frozen=True)
class ChallengeAblationReport:
    family_count: int
    baseline_distinct_signatures: int
    ablations: tuple[ChallengeAblation, ...]
    essential_families: tuple[str, ...]
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "ablation measures finite verdict-signature discrimination under supplied candidates and frozen evaluator; it is not semantic necessity"
    )


def challenge_family_ablation(
    candidate_bases: dict[str, Iterable[str]],
    rules: Iterable[Rule],
    families: Iterable[ProbeFamily],
    evaluator: FrozenEvaluator,
    authority: ChallengeAuthority,
) -> ChallengeAblationReport:
    family_tuple = tuple(families)
    if not candidate_bases or not family_tuple:
        return ChallengeAblationReport(
            len(family_tuple), 0, (), (), "HOLD", ("missing_candidates_or_challenge_families",)
        )
    if not authority.independent or evaluator.evaluator_id in {
        authority.generator_id,
        authority.verifier_id,
    }:
        return ChallengeAblationReport(
            len(family_tuple), 0, (), (), "HOLD", ("challenge_evaluation_authority_not_separated",)
        )

    ordered_rules = tuple(rules)

    def signatures(selected: tuple[ProbeFamily, ...]) -> dict[str, tuple[bool, ...]]:
        result = {str(candidate_id): [] for candidate_id in candidate_bases}
        for family in selected:
            report = evaluate_frozen_challenge(
                candidate_bases, ordered_rules, family, evaluator, authority
            )
            by_id = {item.candidate_id: item.passed for item in report.outcomes}
            for candidate_id in result:
                result[candidate_id].append(by_id[candidate_id])
        return {key: tuple(value) for key, value in result.items()}

    baseline = signatures(family_tuple)
    baseline_distinct = len(set(baseline.values()))
    ablations: list[ChallengeAblation] = []
    for index, family in enumerate(family_tuple):
        reduced = family_tuple[:index] + family_tuple[index + 1 :]
        reduced_signatures = signatures(reduced)
        distinct_after = len(set(reduced_signatures.values()))
        ablations.append(
            ChallengeAblation(
                removed_family=family.name,
                distinct_signatures_before=baseline_distinct,
                distinct_signatures_after=distinct_after,
                discriminative_loss=max(0, baseline_distinct - distinct_after),
            )
        )
    essential = tuple(sorted(item.removed_family for item in ablations if item.discriminative_loss > 0))
    blockers: list[str] = []
    if baseline_distinct <= 1:
        blockers.append("challenge_family_set_not_discriminating")
    if not essential:
        blockers.append("no_individually_essential_challenge_family")
    return ChallengeAblationReport(
        family_count=len(family_tuple),
        baseline_distinct_signatures=baseline_distinct,
        ablations=tuple(ablations),
        essential_families=essential,
        oak_status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
    )


@dataclass(frozen=True)
class AdaptiveStopReport:
    decision: str
    observation_count: int
    window: int
    recent_mean_verified_gain: float
    threshold: float
    oak_status: str
    blockers: tuple[str, ...]
    oak_boundary: str = (
        "STOP means recent supplied verified-gain trace is below the declared marginal threshold; it is not proof that no future useful challenge exists"
    )


def adaptive_information_stop(
    verified_gain_trace: Iterable[float],
    *,
    window: int = 3,
    min_mean_gain: float = 0.05,
) -> AdaptiveStopReport:
    if window < 1:
        raise ValueError("window must be >= 1")
    if min_mean_gain < 0.0:
        raise ValueError("min_mean_gain must be >= 0")
    gains = tuple(float(value) for value in verified_gain_trace)
    if any(not isfinite(value) for value in gains):
        raise ValueError("verified gain trace must be finite")
    if len(gains) < window:
        return AdaptiveStopReport(
            "HOLD", len(gains), window, 0.0, min_mean_gain, "HOLD", ("insufficient_gain_history",)
        )
    recent = gains[-window:]
    recent_mean = sum(recent) / window
    decision = "STOP" if recent_mean < min_mean_gain else "CONTINUE"
    return AdaptiveStopReport(
        decision,
        len(gains),
        window,
        recent_mean,
        min_mean_gain,
        "PASS",
        (),
    )
