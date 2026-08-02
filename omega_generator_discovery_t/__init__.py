"""Ω-GENERATOR-DISCOVERY-STACK public API."""
from .autolab import ExperimentCandidate, ExperimentDecision, prioritize_experiments
from .campaign import (
    CampaignAxes,
    CampaignEmitter,
    CampaignEmissionReport,
    CampaignPartition,
    CampaignSpec,
    benchmark_addition,
    generator_addition,
    iter_generator_bundles,
    load_campaign_spec,
    mixed_radix_decode,
    partition_campaign,
    stream_digest,
)
from .campaign_scale import (
    PROFILE_MULTIPLIERS,
    FrontierDecision,
    FrontierLedger,
    FrontierObservation,
    FrontierPolicy,
    ScaleEpoch,
    ScalePartition,
    ScalePlan,
    ScalePlanner,
    ScalePolicy,
    ValidationPolicy,
    ValidationReport,
    decide_next_frontier,
    epoch_spec,
    epochize_record,
    iter_epoch_bundles,
    resolve_target_records,
    validate_epoch_range,
    write_partition_matrix,
)
from .campaign_scale_emitter import ScaleEmissionReport, ScalePartitionEmitter
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
    "AffineGenerator1D", "CampaignAxes", "CampaignEmitter",
    "CampaignEmissionReport", "CampaignPartition", "CampaignSpec",
    "EpistemicTransition", "ExperimentCandidate", "ExperimentDecision",
    "FRONTS", "FrontSpec", "FrontierDecision", "FrontierLedger",
    "FrontierObservation", "FrontierPolicy", "GeneratorSyndrome",
    "HolonomyReport", "InstrumentProtocol", "LinearGeneratorOperator",
    "MorphIR", "OrderExperiment", "PROFILE_MULTIPLIERS", "ScaleEmissionReport",
    "ScaleEpoch", "ScalePartition", "ScalePartitionEmitter", "ScalePlan",
    "ScalePlanner", "ScalePolicy", "SpectralMorph", "ValidationPolicy",
    "ValidationReport", "benchmark_addition", "compare_spectra",
    "compile_morph_ir", "compile_protocol", "crystal_holonomy",
    "decide_next_frontier", "design_order_experiment", "epoch_spec",
    "epochize_record", "evidence_growth_transition", "fit_scalar_generator",
    "front_registry", "generator_addition", "generator_syndrome",
    "identify_affine_1d", "iter_epoch_bundles", "iter_generator_bundles",
    "load_campaign_spec", "lorentzian", "mixed_radix_decode", "mixture",
    "partition_campaign", "prioritize_experiments", "resolve_target_records",
    "semigroup_defect", "stream_digest", "validate_epoch_range",
    "write_partition_matrix",
]

__version__ = "0.3.0"
