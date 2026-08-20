from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


class PrerequisiteAblationError(ValueError):
    """Raised when a prerequisite ablation comparison is not structurally usable."""


def _scores(values: tuple[float, ...], field: str) -> tuple[float, ...]:
    if not values:
        raise PrerequisiteAblationError(f"{field} must be non-empty")
    clean = tuple(float(v) for v in values)
    if any(v < 0.0 or v > 1.0 for v in clean):
        raise PrerequisiteAblationError(f"{field} values must be within [0, 1]")
    return clean


@dataclass(frozen=True)
class PrerequisiteAblationCase:
    case_id: str
    prerequisite_id: str
    target_id: str
    retained_scores: tuple[float, ...]
    ablated_scores: tuple[float, ...]
    assessment_digest: str
    same_frozen_assessment: bool
    comparable_sampling: bool
    randomized_assignment: bool = False
    independent_evaluator: bool = False

    def __post_init__(self) -> None:
        for field_name in ("case_id", "prerequisite_id", "target_id", "assessment_digest"):
            value = getattr(self, field_name).strip()
            if not value:
                raise PrerequisiteAblationError(f"{field_name} must be non-empty")
            object.__setattr__(self, field_name, value)
        object.__setattr__(self, "retained_scores", _scores(self.retained_scores, "retained_scores"))
        object.__setattr__(self, "ablated_scores", _scores(self.ablated_scores, "ablated_scores"))


@dataclass(frozen=True)
class PrerequisiteAblationResult:
    case_id: str
    retained_mean: float
    ablated_mean: float
    observed_delta: float
    status: str
    causal_review_eligible: bool
    prerequisite_redundancy_proven: bool = False
    prerequisite_removal_authorized: bool = False


def evaluate_prerequisite_ablation(
    case: PrerequisiteAblationCase,
    *,
    tolerance: float = 0.02,
) -> PrerequisiteAblationResult:
    """Evaluate a bounded prerequisite ablation fixture.

    `CANDIDATE_REDUNDANT_UNDER_FIXTURE` is a review signal only. It is never proof
    that the prerequisite is globally unnecessary and never authorizes graph edits.
    """

    tolerance = float(tolerance)
    if tolerance < 0.0:
        raise PrerequisiteAblationError("tolerance must be non-negative")

    retained_mean = mean(case.retained_scores)
    ablated_mean = mean(case.ablated_scores)
    delta = ablated_mean - retained_mean
    comparable = case.same_frozen_assessment and case.comparable_sampling
    eligible = all(
        (
            comparable,
            case.randomized_assignment,
            case.independent_evaluator,
        )
    )

    if not comparable:
        status = "INCOMPARABLE_FIXTURE"
    elif delta < -tolerance:
        status = "OBSERVED_PERFORMANCE_DROP"
    else:
        status = "CANDIDATE_REDUNDANT_UNDER_FIXTURE"

    return PrerequisiteAblationResult(
        case_id=case.case_id,
        retained_mean=retained_mean,
        ablated_mean=ablated_mean,
        observed_delta=delta,
        status=status,
        causal_review_eligible=eligible,
    )
