"""Ω-META-SCIENCE-FOUNDRY-T∞² executable research kernel."""

from .benchmark import build_fixture, run_benchmark, run_strategy
from .discovery import (
    ArbitrageDecision,
    CounterexampleCandidate,
    DiscoveryDynamicsReport,
    EpistemicJacobianReport,
    InvariantTransportMap,
    InvariantTransportReport,
    RepresentationRoute,
    ResidualGenome,
    ScientificIR,
    TheoryAdapter,
    compile_counterexample,
    compile_residual_genome,
    epistemic_jacobian,
    representation_arbitrage,
    run_discovery_dynamics_demo,
    transport_invariants,
    unknown_unknown_radar,
)
from .models import BenchmarkReport, Experiment, StrategyResult, TheoryGenome
from .oak import FAULT_TYPES, evaluate_oak, meta_oak_mutation_campaign

__all__ = [
    "ArbitrageDecision",
    "BenchmarkReport",
    "CounterexampleCandidate",
    "DiscoveryDynamicsReport",
    "EpistemicJacobianReport",
    "Experiment",
    "FAULT_TYPES",
    "InvariantTransportMap",
    "InvariantTransportReport",
    "RepresentationRoute",
    "ResidualGenome",
    "ScientificIR",
    "StrategyResult",
    "TheoryAdapter",
    "TheoryGenome",
    "build_fixture",
    "compile_counterexample",
    "compile_residual_genome",
    "epistemic_jacobian",
    "evaluate_oak",
    "meta_oak_mutation_campaign",
    "representation_arbitrage",
    "run_benchmark",
    "run_discovery_dynamics_demo",
    "run_strategy",
    "transport_invariants",
    "unknown_unknown_radar",
]

__version__ = "0.2.0"
