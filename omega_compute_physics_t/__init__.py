"""Ω-COMPUTE-PHYSICS-T∞ / Ω-COMPLEXITY-ATLAS-T∞.

Empirical, OAK-safe resource modelling for functions and pipelines.

Important epistemic rule: fitted finite-domain scaling is empirical evidence, not a
mathematical proof of asymptotic Big-O/Theta complexity.
"""

from .active import (
    ExperimentCandidate,
    discriminating_experiment,
    geometric_design_space,
    rank_experiments,
    select_next_experiments,
)
from .atlas import ComplexityAtlas, EmpiricalResourceModel, ResourceSample
from .budget import (
    BudgetCompileReport,
    CandidateEvaluation,
    ResourceConstraint,
    compile_budget,
    pareto_front,
    quality_per_cost,
)
from .complexity_diff import ComplexityDiffReport, compare_models, geometric_sweep
from .profiler import ProfileResult, profile_call, profile_pipeline
from .validation import (
    ConformalInterval,
    DriftReport,
    ModelCandidate,
    ValidatedResourceModel,
    detect_drift,
    fit_validated_resource_model,
)

__all__ = [
    "ComplexityAtlas",
    "EmpiricalResourceModel",
    "ResourceSample",
    "ProfileResult",
    "profile_call",
    "profile_pipeline",
    "ModelCandidate",
    "ValidatedResourceModel",
    "ConformalInterval",
    "DriftReport",
    "fit_validated_resource_model",
    "detect_drift",
    "ComplexityDiffReport",
    "compare_models",
    "geometric_sweep",
    "ExperimentCandidate",
    "geometric_design_space",
    "rank_experiments",
    "select_next_experiments",
    "discriminating_experiment",
    "ResourceConstraint",
    "CandidateEvaluation",
    "BudgetCompileReport",
    "compile_budget",
    "pareto_front",
    "quality_per_cost",
]

__version__ = "0.3.0"
