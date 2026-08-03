"""Experiment compilation and bounded adaptive scheduling."""
from __future__ import annotations
from .factorial import full_factorial_design, fractional_half_design
from .models import ExperimentDesign, canonical_components


def compile_design(components, *, design_type="auto", replicates=1, full_cap=8) -> ExperimentDesign:
    items=canonical_components(components)
    if design_type=="full" or (design_type=="auto" and len(items)<=full_cap):
        return full_factorial_design(items,replicates=replicates)
    if design_type in ("fractional","auto"):
        return fractional_half_design(items)
    raise ValueError(f"unknown design_type {design_type}")


def missing_configurations(design: ExperimentDesign, observations: dict[frozenset[str],float]) -> list[tuple[str,...]]:
    return [run.active for run in design.runs if frozenset(run.active) not in observations]


def next_adaptive_run(design: ExperimentDesign, observations: dict[frozenset[str],float], uncertainties: dict[frozenset[str],float]|None=None) -> tuple[str,...]|None:
    missing=missing_configurations(design,observations)
    if not missing: return None
    uncertainties=uncertainties or {}
    return sorted(missing,key=lambda active:(-uncertainties.get(frozenset(active),1.0),len(active),active))[0]


def stopping_decision(*, critical_failure=False, simpler_baseline_dominates=False, interval_low=None, interval_high=None, target=0.0) -> str:
    if critical_failure: return "STOP_CRITICAL_FAILURE"
    if simpler_baseline_dominates: return "STOP_SIMPLER_BASELINE_DOMINATES"
    if interval_high is not None and interval_high<target: return "STOP_NEGATIVE_INTERACTION"
    if interval_low is not None and interval_low>target: return "STOP_POSITIVE_DECISION_STABLE"
    return "CONTINUE"
