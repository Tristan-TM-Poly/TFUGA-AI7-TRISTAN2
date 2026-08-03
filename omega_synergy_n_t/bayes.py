"""Small conjugate Gaussian updater for interaction estimates.

This is a decision aid, not Bayes-factor proof and not a replacement for causal design.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import erf,sqrt

@dataclass(frozen=True,slots=True)
class NormalBelief:
    mean: float=0.0
    standard_deviation: float=1.0
    def __post_init__(self):
        if self.standard_deviation<=0: raise ValueError("standard_deviation must be positive")


def update(prior: NormalBelief,observation: float,standard_error: float) -> NormalBelief:
    if standard_error<=0: raise ValueError("standard_error must be positive")
    p0=1/(prior.standard_deviation**2); p1=1/(standard_error**2)
    variance=1/(p0+p1); mean=variance*(p0*prior.mean+p1*observation)
    return NormalBelief(mean,sqrt(variance))


def probability_greater_than(belief: NormalBelief,threshold: float=0.0) -> float:
    z=(threshold-belief.mean)/(belief.standard_deviation*sqrt(2))
    return .5*(1-erf(z))


def hypothesis_packet(belief: NormalBelief,threshold: float=0.0) -> dict:
    p=probability_greater_than(belief,threshold)
    return {"posterior_mean":belief.mean,"posterior_standard_deviation":belief.standard_deviation,
            "probability_positive":p,"hypotheses":{"H_plus":p,"H_not_plus":1-p},
            "causal_claimed":False,"decision_authority":"review_only"}
