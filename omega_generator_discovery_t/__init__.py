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
from .ultra_catalog import (
    UltraAuditReport,
    UltraGeneratorRecord,
    audit_ultra_catalog,
    catalog_statistics,
    deterministic_validation_sample,
    export_subatlas,
    get_generator,
    load_manifest,
    query_generators,
    related_bundle,
)

__all__ = [
    "AffineGenerator1D", "EpistemicTransition", "ExperimentCandidate",
    "ExperimentDecision", "GeneratorSyndrome", "HolonomyReport",
    "InstrumentProtocol", "LinearGeneratorOperator", "MorphIR",
    "FRONTS", "FrontSpec", "OrderExperiment", "SpectralMorph",
    "UltraAuditReport", "UltraGeneratorRecord",
    "audit_ultra_catalog", "catalog_statistics", "compare_spectra",
    "compile_morph_ir", "compile_protocol", "crystal_holonomy",
    "design_order_experiment", "deterministic_validation_sample",
    "evidence_growth_transition", "export_subatlas",
    "fit_scalar_generator", "front_registry", "generator_syndrome",
    "get_generator", "identify_affine_1d", "load_manifest",
    "lorentzian", "mixture", "prioritize_experiments",
    "query_generators", "related_bundle", "semigroup_defect",
]

__version__ = "0.3.0"
