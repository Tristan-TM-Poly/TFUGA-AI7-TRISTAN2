"""Numerical, provenance-aware spectral evidence scoring.

Family compatibility is scored; molecular identity is never inferred from a
single band or modality.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import prod
from typing import Iterable, Mapping, Sequence

from .evidence_models import Peak, SpectralObservation


@dataclass(frozen=True, slots=True)
class BandRange:
    label: str
    minimum: float
    maximum: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.minimum > self.maximum or self.weight <= 0:
            raise ValueError("invalid band range")

    def matches(self, peak: Peak) -> bool:
        return peak.position + peak.tolerance >= self.minimum and peak.position - peak.tolerance <= self.maximum


@dataclass(frozen=True, slots=True)
class NumericSpectralRule:
    rule_id: str
    family: str
    modality: str
    required: tuple[BandRange, ...]
    optional: tuple[BandRange, ...] = ()
    counters: tuple[BandRange, ...] = ()
    provenance: str = "curated_seed_rule_r03"
    domain: Mapping[str, str] | None = None
    status: str = "family_level_numeric_expectation"


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    rule_id: str
    family: str
    modality: str
    score: float
    matched_required: tuple[str, ...]
    missing_required: tuple[str, ...]
    matched_optional: tuple[str, ...]
    matched_counters: tuple[str, ...]
    source_quality: float
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _matched_labels(ranges: Sequence[BandRange], peaks: Sequence[Peak]) -> tuple[str, ...]:
    return tuple(item.label for item in ranges if any(item.matches(peak) for peak in peaks))


def evaluate_numeric_rule(
    rule: NumericSpectralRule,
    observation: SpectralObservation,
    *,
    source_quality: float,
) -> RuleEvaluation:
    if observation.modality != rule.modality:
        raise ValueError("observation modality does not match rule modality")
    if not 0 <= source_quality <= 1:
        raise ValueError("source quality must be in [0,1]")
    required_matches = _matched_labels(rule.required, observation.peaks)
    optional_matches = _matched_labels(rule.optional, observation.peaks)
    counter_matches = _matched_labels(rule.counters, observation.peaks)
    required_weight = sum(item.weight for item in rule.required) or 1.0
    matched_required_weight = sum(item.weight for item in rule.required if item.label in required_matches)
    optional_weight = sum(item.weight for item in rule.optional) or 1.0
    matched_optional_weight = sum(item.weight for item in rule.optional if item.label in optional_matches)
    counter_weight = sum(item.weight for item in rule.counters) or 1.0
    matched_counter_weight = sum(item.weight for item in rule.counters if item.label in counter_matches)
    required_fraction = matched_required_weight / required_weight
    optional_bonus = 0.15 * matched_optional_weight / optional_weight if rule.optional else 0.0
    counter_penalty = 0.60 * matched_counter_weight / counter_weight if rule.counters else 0.0
    score = max(0.0, min(1.0, (required_fraction + optional_bonus - counter_penalty) * source_quality))
    missing = tuple(item.label for item in rule.required if item.label not in required_matches)
    status = "family_compatible" if score >= 0.65 and not counter_matches else "insufficient_or_conflicting"
    return RuleEvaluation(
        rule_id=rule.rule_id,
        family=rule.family,
        modality=rule.modality,
        score=round(score, 6),
        matched_required=required_matches,
        missing_required=missing,
        matched_optional=optional_matches,
        matched_counters=counter_matches,
        source_quality=source_quality,
        status=status,
    )


def fuse_rule_evaluations(evaluations: Iterable[RuleEvaluation]) -> dict[str, object]:
    items = tuple(evaluations)
    if not items:
        return {"score": 0.0, "modalities": 0, "contradictions": 0, "status": "no_evidence"}
    modalities = {item.modality for item in items if item.score > 0}
    contradictions = sum(bool(item.matched_counters) for item in items)
    # Noisy-OR rewards independent support without pretending independence is exact.
    combined = 1.0 - prod(1.0 - item.score for item in items)
    combined *= max(0.0, 1.0 - 0.25 * contradictions)
    combined = round(max(0.0, min(1.0, combined)), 6)
    if contradictions:
        status = "conflicted_evidence"
    elif len(modalities) >= 2 and combined >= 0.85:
        status = "multimodal_family_support"
    elif combined >= 0.60:
        status = "family_compatible"
    else:
        status = "insufficient_evidence"
    return {
        "score": combined,
        "modalities": len(modalities),
        "contradictions": contradictions,
        "status": status,
        "rule_ids": [item.rule_id for item in items],
    }
