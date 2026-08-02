"""Ω-RE-T∞ — OAK-safe active reconstruction of hidden mechanisms."""

from .active import select_experiment
from .bayes import posterior_entropy_bits, score_candidates
from .campaign import reconstruct_fsm
from .evidence import EvidenceLedger
from .fsm import MealyMachine, canonical_demo_machine, enumerate_mealy_machines
from .models import (
    AuthorizationMode,
    AuthorizationScope,
    CampaignResult,
    ClaimStatus,
    EvidenceRecord,
    Experiment,
    Observation,
    OAKMetricVector,
    OAKReport,
    RiskClass,
)
from .twin import CounterfactualTwin, TwinPrediction

__all__ = [
    "AuthorizationMode",
    "AuthorizationScope",
    "CampaignResult",
    "ClaimStatus",
    "CounterfactualTwin",
    "EvidenceLedger",
    "EvidenceRecord",
    "Experiment",
    "MealyMachine",
    "Observation",
    "OAKMetricVector",
    "OAKReport",
    "RiskClass",
    "TwinPrediction",
    "canonical_demo_machine",
    "enumerate_mealy_machines",
    "posterior_entropy_bits",
    "reconstruct_fsm",
    "score_candidates",
    "select_experiment",
]
