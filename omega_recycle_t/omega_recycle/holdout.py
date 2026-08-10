from __future__ import annotations
from dataclasses import dataclass, field
from .campaign import PredictionCase, PredictionCampaignReport, evaluate_prediction_campaign

@dataclass(frozen=True, slots=True)
class TemporalPredictionCase:
    case_id: str
    period: int
    observed_value: float
    predictions: dict[str,float] = field(default_factory=dict)
    weight: float = 1.0

@dataclass(frozen=True, slots=True)
class TemporalHoldoutReport:
    train_count: int
    test_count: int
    holdout_start: int
    campaign: PredictionCampaignReport
    claim_boundary: str = "predeclared_temporal_holdout_scoring_only_not_model_training_or_causal_validation"

def evaluate_temporal_holdout(cases:tuple[TemporalPredictionCase,...], *, holdout_start:int, canonical_method:str)->TemporalHoldoutReport:
    train=tuple(c for c in cases if c.period<holdout_start)
    test=tuple(c for c in cases if c.period>=holdout_start)
    if not train: raise ValueError("temporal holdout requires at least one pre-holdout case")
    if not test: raise ValueError("temporal holdout requires at least one held-out case")
    campaign=evaluate_prediction_campaign(
        tuple(PredictionCase(c.case_id,c.observed_value,c.predictions,c.weight) for c in test),
        canonical_method=canonical_method
    )
    return TemporalHoldoutReport(len(train),len(test),holdout_start,campaign)
