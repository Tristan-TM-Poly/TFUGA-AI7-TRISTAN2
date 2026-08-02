"""Ω-GENERATOR-DISCOVERY-STACK public API."""
from .autolab import ExperimentCandidate, ExperimentDecision, prioritize_experiments
from .core import (
    AffineGenerator1D,
    GeneratorSyndrome,
    LinearGeneratorOperator,
    MorphIR,
    OrderExperiment,
    compile_morph_ir,
    design_order_experiment,
    fit_scalar_generator,
    generator_syndrome,
    identify_affine_1d,
    semigroup_defect,
)
from .crystal import HolonomyReport, crystal_holonomy
from .epistemic import EpistemicTransition, evidence_growth_transition
from .fronts import FRONTS, FrontSpec, front_registry
from .protocol import InstrumentProtocol, compile_protocol
from .spectral import SpectralMorph, compare_spectra, lorentzian, mixture

__all__ = [
    "AffineGenerator1D", "EpistemicTransition", "ExperimentCandidate",
    "ExperimentDecision", "GeneratorSyndrome", "HolonomyReport",
    "InstrumentProtocol", "LinearGeneratorOperator", "MorphIR",
    "FRONTS", "FrontSpec", "OrderExperiment", "SpectralMorph",
    "compare_spectra", "compile_morph_ir", "compile_protocol",
    "crystal_holonomy", "design_order_experiment",
    "evidence_growth_transition", "fit_scalar_generator",
    "front_registry", "generator_syndrome", "identify_affine_1d",
    "lorentzian", "mixture", "prioritize_experiments",
    "semigroup_defect",
]

__version__ = "0.1.0"
