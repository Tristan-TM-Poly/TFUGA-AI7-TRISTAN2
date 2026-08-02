"""Hypothesis portfolio scoring and adaptive quality governance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Sequence

from .models import ConductorDecision, Hypothesis


_EPS = 1e-12


@dataclass(frozen=True)
class ScoredHypothesis:
    hypothesis_id: str
    statement: str
    raw_priority: float
    normalized_priority: float
    expected_information_per_cost: float
    risk_penalty: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BudgetAllocation:
    hypothesis_id: str
    allocation: float
    minimum_test_budget: float
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityObservation:
    generated_objects: int
    unique_objects: int
    formalized_claims: int
    claims_with_evidence: int
    claims_with_falsification: int
    externally_validated_claims: int
    duplicate_objects: int
    orphan_objects: int
    circular_evidence_links: int
    repeated_errors_prevented: int
    repeated_errors_observed: int

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in asdict(self).items():
            if value < 0:
                errors.append(f"{name} must be non-negative")
        if self.unique_objects > self.generated_objects:
            errors.append("unique_objects cannot exceed generated_objects")
        if self.formalized_claims > self.unique_objects:
            errors.append("formalized_claims cannot exceed unique_objects")
        if self.claims_with_evidence > self.formalized_claims:
            errors.append("claims_with_evidence cannot exceed formalized_claims")
        if self.claims_with_falsification > self.formalized_claims:
            errors.append("claims_with_falsification cannot exceed formalized_claims")
        if self.externally_validated_claims > self.claims_with_evidence:
            errors.append("externally_validated_claims cannot exceed claims_with_evidence")
        return errors

    @property
    def uniqueness(self) -> float:
        return self.unique_objects / max(self.generated_objects, 1)

    @property
    def evidence_density(self) -> float:
        return self.claims_with_evidence / max(self.formalized_claims, 1)

    @property
    def falsification_coverage(self) -> float:
        return self.claims_with_falsification / max(self.formalized_claims, 1)

    @property
    def external_validation_rate(self) -> float:
        return self.externally_validated_claims / max(self.formalized_claims, 1)

    @property
    def noise_rate(self) -> float:
        noise = self.duplicate_objects + self.orphan_objects + self.circular_evidence_links
        return noise / max(self.generated_objects + self.formalized_claims, 1)

    @property
    def mminus_effectiveness(self) -> float:
        total = self.repeated_errors_prevented + self.repeated_errors_observed
        return self.repeated_errors_prevented / max(total, 1)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["metrics"] = {
            "uniqueness": self.uniqueness,
            "evidence_density": self.evidence_density,
            "falsification_coverage": self.falsification_coverage,
            "external_validation_rate": self.external_validation_rate,
            "noise_rate": self.noise_rate,
            "mminus_effectiveness": self.mminus_effectiveness,
        }
        return data


@dataclass(frozen=True)
class QualityDecision:
    decision: ConductorDecision
    reasons: tuple[str, ...]
    recommended_generation_factor: float
    recommended_validation_factor: float
    recommended_externalization_factor: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


def hypothesis_priority(hypothesis: Hypothesis) -> float:
    """Compute the routing priority described in the conceptual architecture.

    This score is a heuristic.  It must be calibrated against real outcomes and
    never treated as a probability, proof, or autonomous funding decision.
    """

    errors = hypothesis.validate()
    if errors:
        raise ValueError("; ".join(errors))
    numerator = (
        hypothesis.value_potential
        * hypothesis.information_gain
        * hypothesis.falsifiability
        * hypothesis.reusability
    )
    denominator = (
        (hypothesis.cost + _EPS)
        * (hypothesis.time_cost + _EPS)
        * (hypothesis.operational_uncertainty + 0.05)
        * (hypothesis.dependency_load + 0.05)
    )
    return numerator / denominator


def score_hypotheses(hypotheses: Iterable[Hypothesis]) -> list[ScoredHypothesis]:
    raw: list[tuple[Hypothesis, float]] = []
    for hypothesis in hypotheses:
        score = hypothesis_priority(hypothesis)
        raw.append((hypothesis, score))
    raw.sort(key=lambda pair: (-pair[1], pair[0].hypothesis_id))
    total = sum(score for _, score in raw) or 1.0
    result: list[ScoredHypothesis] = []
    for hypothesis, score in raw:
        risk = (
            hypothesis.operational_uncertainty
            + min(1.0, hypothesis.dependency_load / (1.0 + hypothesis.dependency_load))
        ) / 2
        reasons = (
            f"information_gain={hypothesis.information_gain:.3f}",
            f"falsifiability={hypothesis.falsifiability:.3f}",
            f"value_potential={hypothesis.value_potential:.3f}",
            f"risk_penalty={risk:.3f}",
        )
        result.append(
            ScoredHypothesis(
                hypothesis_id=hypothesis.hypothesis_id,
                statement=hypothesis.statement,
                raw_priority=score,
                normalized_priority=score / total,
                expected_information_per_cost=(
                    hypothesis.information_gain / max(hypothesis.cost, _EPS)
                ),
                risk_penalty=risk,
                reasons=reasons,
            )
        )
    return result


def allocate_budget(
    scored: Sequence[ScoredHypothesis],
    total_budget: float,
    *,
    minimum_test_budget: float = 0.0,
    max_share: float = 0.5,
) -> list[BudgetAllocation]:
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    if minimum_test_budget < 0:
        raise ValueError("minimum_test_budget must be non-negative")
    if not 0 < max_share <= 1:
        raise ValueError("max_share must be in (0,1]")
    if not scored:
        return []
    minimum_total = minimum_test_budget * len(scored)
    if minimum_total > total_budget + _EPS:
        raise ValueError("minimum allocations exceed total budget")
    remaining = total_budget - minimum_total
    caps = [total_budget * max_share for _ in scored]
    allocations = [minimum_test_budget for _ in scored]
    active = set(range(len(scored)))
    while remaining > _EPS and active:
        weight_sum = sum(scored[i].normalized_priority for i in active)
        if weight_sum <= _EPS:
            split = remaining / len(active)
            for i in active:
                allocations[i] += split
            remaining = 0.0
            break
        consumed = 0.0
        saturated: set[int] = set()
        for i in sorted(active):
            proposed = remaining * scored[i].normalized_priority / weight_sum
            capacity = max(0.0, caps[i] - allocations[i])
            delta = min(proposed, capacity)
            allocations[i] += delta
            consumed += delta
            if capacity - delta <= _EPS:
                saturated.add(i)
        if consumed <= _EPS:
            break
        remaining -= consumed
        active -= saturated
    # Numerical residue is routed deterministically to available slots.
    if remaining > _EPS:
        for i in range(len(scored)):
            capacity = max(0.0, caps[i] - allocations[i])
            delta = min(remaining, capacity)
            allocations[i] += delta
            remaining -= delta
            if remaining <= _EPS:
                break
    return [
        BudgetAllocation(
            hypothesis_id=item.hypothesis_id,
            allocation=allocations[index],
            minimum_test_budget=minimum_test_budget,
            rank=index + 1,
        )
        for index, item in enumerate(scored)
    ]


def decide_quality(observation: QualityObservation) -> QualityDecision:
    errors = observation.validate()
    if errors:
        raise ValueError("; ".join(errors))
    reasons: list[str] = []
    if observation.orphan_objects > 0 or observation.circular_evidence_links > 0:
        reasons.append("reference_integrity_failure")
        return QualityDecision(
            decision=ConductorDecision.REDESIGN,
            reasons=tuple(reasons),
            recommended_generation_factor=0.0,
            recommended_validation_factor=2.0,
            recommended_externalization_factor=0.0,
        )
    if observation.noise_rate > 0.15:
        reasons.append("noise_rate_above_0.15")
        return QualityDecision(
            decision=ConductorDecision.RESHARD,
            reasons=tuple(reasons),
            recommended_generation_factor=0.5,
            recommended_validation_factor=1.75,
            recommended_externalization_factor=0.25,
        )
    if observation.evidence_density < 0.5 or observation.falsification_coverage < 0.7:
        reasons.append("evidence_or_falsification_debt")
        return QualityDecision(
            decision=ConductorDecision.HOLD,
            reasons=tuple(reasons),
            recommended_generation_factor=0.25,
            recommended_validation_factor=2.0,
            recommended_externalization_factor=0.25,
        )
    if observation.external_validation_rate < 0.05:
        reasons.append("external_validation_bottleneck")
        return QualityDecision(
            decision=ConductorDecision.HOLD,
            reasons=tuple(reasons),
            recommended_generation_factor=0.5,
            recommended_validation_factor=1.5,
            recommended_externalization_factor=2.0,
        )
    if observation.mminus_effectiveness < 0.5 and observation.repeated_errors_observed > 0:
        reasons.append("negative_memory_not_reducing_recurrence")
        return QualityDecision(
            decision=ConductorDecision.REDESIGN,
            reasons=tuple(reasons),
            recommended_generation_factor=0.25,
            recommended_validation_factor=2.0,
            recommended_externalization_factor=1.0,
        )
    reasons.append("quality_gates_passed")
    return QualityDecision(
        decision=ConductorDecision.EXPAND,
        reasons=tuple(reasons),
        recommended_generation_factor=2.0,
        recommended_validation_factor=1.5,
        recommended_externalization_factor=1.5,
    )
