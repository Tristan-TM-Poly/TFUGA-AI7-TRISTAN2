from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


class LearningRealityError(ValueError):
    """Raised when a learning/reality observation is structurally invalid."""


def _non_empty(value: str, field: str) -> str:
    clean = value.strip()
    if not clean:
        raise LearningRealityError(f"{field} must be non-empty")
    return clean


def _score(value: float, field: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise LearningRealityError(f"{field} must be within [0, 1]")
    return value


@dataclass(frozen=True)
class FrozenAssessment:
    assessment_id: str
    capability_id: str
    item_ids: tuple[str, ...]
    context: str
    version: str
    holdout: bool = False
    generator_exposed: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", _non_empty(self.assessment_id, "assessment_id"))
        object.__setattr__(self, "capability_id", _non_empty(self.capability_id, "capability_id"))
        object.__setattr__(self, "context", _non_empty(self.context, "context"))
        object.__setattr__(self, "version", _non_empty(self.version, "version"))
        clean_items = tuple(item.strip() for item in self.item_ids if item.strip())
        if not clean_items:
            raise LearningRealityError("item_ids must contain at least one item")
        if len(clean_items) != len(set(clean_items)):
            raise LearningRealityError("item_ids must be unique inside a frozen assessment")
        object.__setattr__(self, "item_ids", clean_items)

    def payload(self) -> dict[str, object]:
        return asdict(self)

    def digest(self) -> str:
        canonical = json.dumps(self.payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LearningObservation:
    observation_id: str
    intervention_id: str
    capability_id: str
    assessment_digest: str
    pre_score: float
    post_score: float
    context: str
    randomized_assignment: bool = False
    concurrent_control: bool = False
    independent_evaluator: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation_id", _non_empty(self.observation_id, "observation_id"))
        object.__setattr__(self, "intervention_id", _non_empty(self.intervention_id, "intervention_id"))
        object.__setattr__(self, "capability_id", _non_empty(self.capability_id, "capability_id"))
        object.__setattr__(self, "assessment_digest", _non_empty(self.assessment_digest, "assessment_digest"))
        object.__setattr__(self, "context", _non_empty(self.context, "context"))
        object.__setattr__(self, "pre_score", _score(self.pre_score, "pre_score"))
        object.__setattr__(self, "post_score", _score(self.post_score, "post_score"))


@dataclass(frozen=True)
class LearningGainResult:
    observation_id: str
    observed_delta: float
    status: str
    causal_review_eligible: bool
    causal_claim_proven: bool = False
    credential_awarded: bool = False
    external_action_authorized: bool = False


@dataclass(frozen=True)
class OODProbeResult:
    assessment_id: str
    train_context: str
    eval_context: str
    structurally_ood: bool
    valid_holdout: bool
    score: float
    baseline_score: float | None
    observed_delta_over_baseline: float | None
    transfer_claim_proven: bool = False
    external_action_authorized: bool = False


def measure_learning_gain(
    observation: LearningObservation,
    assessment: FrozenAssessment,
) -> LearningGainResult:
    """Measure an observed pre/post delta bound to a frozen assessment manifest.

    Even with strong design metadata, this function never emits a causal proof.
    """

    if observation.assessment_digest != assessment.digest():
        raise LearningRealityError("observation is not bound to the supplied frozen assessment")
    if observation.capability_id != assessment.capability_id:
        raise LearningRealityError("observation capability does not match assessment capability")
    if observation.context != assessment.context:
        raise LearningRealityError("observation context does not match assessment context")

    delta = observation.post_score - observation.pre_score
    eligible = all(
        (
            observation.randomized_assignment,
            observation.concurrent_control,
            observation.independent_evaluator,
            assessment.holdout,
            not assessment.generator_exposed,
        )
    )
    return LearningGainResult(
        observation_id=observation.observation_id,
        observed_delta=delta,
        status="OBSERVED_GAIN_ONLY",
        causal_review_eligible=eligible,
    )


def evaluate_ood_probe(
    *,
    train_context: str,
    assessment: FrozenAssessment,
    score: float,
    baseline_score: float | None = None,
) -> OODProbeResult:
    """Qualify a bounded OOD probe without promoting it into proof of transfer."""

    train_context = _non_empty(train_context, "train_context")
    score = _score(score, "score")
    baseline = None if baseline_score is None else _score(baseline_score, "baseline_score")
    structurally_ood = train_context != assessment.context
    valid_holdout = assessment.holdout and not assessment.generator_exposed
    delta = None if baseline is None else score - baseline
    return OODProbeResult(
        assessment_id=assessment.assessment_id,
        train_context=train_context,
        eval_context=assessment.context,
        structurally_ood=structurally_ood,
        valid_holdout=valid_holdout,
        score=score,
        baseline_score=baseline,
        observed_delta_over_baseline=delta,
    )


def make_learning_receipt(
    result: LearningGainResult,
    assessment: FrozenAssessment,
) -> dict[str, object]:
    payload = {
        "kind": "omega.university.learning-observation.r0.3",
        "assessment_digest": assessment.digest(),
        "result": asdict(result),
        "boundaries": {
            "observed_gain_is_causal_proof": False,
            "causal_review_eligible_is_causal_proof": False,
            "assessment_is_credential": False,
            "external_action_authorized": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {**payload, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
