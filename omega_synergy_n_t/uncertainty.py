"""Uncertainty, context comparison, and confidence half-life."""
from __future__ import annotations
from math import exp,sqrt
from .models import InteractionEstimate


def rss_standard_error(values) -> float:
    vals=[float(x) for x in values]
    if any(x<0 for x in vals): raise ValueError("standard errors must be non-negative")
    return sqrt(sum(x*x for x in vals))


def decayed_confidence(initial: float, elapsed: float, half_life: float) -> float:
    if not 0<=initial<=1: raise ValueError("initial confidence must be in [0,1]")
    if elapsed<0 or half_life<=0: raise ValueError("elapsed must be non-negative and half_life positive")
    return initial*exp(-0.6931471805599453*elapsed/half_life)


def compare_contexts(a: InteractionEstimate,b: InteractionEstimate,z: float=1.96) -> dict:
    if a.components!=b.components: raise ValueError("context comparison requires same coalition")
    difference=b.proper_interaction-a.proper_interaction
    se=rss_standard_error((a.standard_error,b.standard_error))
    low=difference-z*se; high=difference+z*se
    if low>0: status="INCREASED"
    elif high<0: status="DECREASED"
    else: status="INCONCLUSIVE"
    return {"components":list(a.components),"from_context":a.context_id,"to_context":b.context_id,
            "difference":difference,"standard_error":se,"interval":[low,high],"status":status,
            "causal_claimed":False}
