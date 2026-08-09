from __future__ import annotations

from math import exp, isfinite, log

from .models import SynapseState


def effective_synaptic_weight(state: SynapseState, *, confidence_adjusted: bool = False) -> float:
    """Project a multidimensional synapse state to an effective scalar.

    The projection is deliberately transparent so richer models can be tested
    against a scalar-weight baseline. Uncertainty is a confidence term, not a
    biological causal factor; it only changes the result when explicitly asked.
    """

    weight = (
        state.release_probability
        * state.quantal_scale
        * state.short_term_gain
        * state.long_term_gain
        * state.astrocytic_context
        * state.neuromodulatory_context
        * state.metabolic_context
    )
    if confidence_adjusted:
        weight *= 1.0 - state.uncertainty
    return weight


def log_plasticity_update(weight: float, relative_rate: float, dt: float) -> float:
    """Multiplicative LOG/EXP plasticity update: w(t+dt)=w(t) exp(rho*dt)."""

    if not isfinite(weight) or weight <= 0.0:
        raise ValueError("weight must be finite and > 0 for a log-domain update")
    if not isfinite(relative_rate) or not isfinite(dt):
        raise ValueError("relative_rate and dt must be finite")
    return exp(log(weight) + relative_rate * dt)


def scalar_weight_baseline(state: SynapseState) -> float:
    """Minimal baseline that intentionally ignores contextual state."""

    return state.release_probability * state.quantal_scale


def contextual_gain(state: SynapseState) -> float:
    baseline = scalar_weight_baseline(state)
    rich = effective_synaptic_weight(state)
    if baseline == 0.0:
        return 0.0 if rich == 0.0 else float("inf")
    return rich / baseline
