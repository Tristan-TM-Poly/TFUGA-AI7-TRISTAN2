"""Ω-SPACE-HG-T∞: OAK-safe hypergraph spacecraft research kernel."""

from .atlas import (
    ENVIRONMENT_CLASSES,
    FIDELITY_LEVELS,
    MISSION_CLASSES,
    SIMULATION_DOMAINS,
    SUBSYSTEM_CLASSES,
    VEHICLE_AND_MODULE_CLASSES,
    atlas_manifest,
    select_atlas_slice,
)
from .hypergraph import SpaceHyperedge, SpaceHypergraph, SpaceNode, build_spacecraft_hypergraph
from .io import emit_json, load_mission, mission_from_dict
from .mission import DEFAULT_SUBSYSTEMS, compile_mission_hypergraph, simulate_mission
from .models import (
    MissionConfig,
    MissionMetrics,
    MissionResult,
    OrbitState,
    SimulationPoint,
    SpacecraftConfig,
)
from .oak import EARTH_MU_M3_S2, EARTH_RADIUS_M, canonical_6u_mission, run_oak_benchmarks
from .optimization import (
    DesignAddress,
    DesignEvaluation,
    UnboundedDesignFrontier,
    evaluate_design,
    optimize_designs,
    pareto_front,
)
from .orbit import (
    circular_orbit_state,
    orbital_period_s,
    propagate_two_body,
    relative_energy_drift,
    semimajor_axis_m,
    specific_angular_momentum,
    specific_energy,
    velocity_verlet_step,
)

__all__ = [
    "DEFAULT_SUBSYSTEMS",
    "DesignAddress",
    "DesignEvaluation",
    "EARTH_MU_M3_S2",
    "EARTH_RADIUS_M",
    "ENVIRONMENT_CLASSES",
    "FIDELITY_LEVELS",
    "MISSION_CLASSES",
    "MissionConfig",
    "MissionMetrics",
    "MissionResult",
    "OrbitState",
    "SIMULATION_DOMAINS",
    "SUBSYSTEM_CLASSES",
    "SimulationPoint",
    "SpaceHyperedge",
    "SpaceHypergraph",
    "SpaceNode",
    "SpacecraftConfig",
    "UnboundedDesignFrontier",
    "VEHICLE_AND_MODULE_CLASSES",
    "atlas_manifest",
    "build_spacecraft_hypergraph",
    "canonical_6u_mission",
    "circular_orbit_state",
    "compile_mission_hypergraph",
    "emit_json",
    "evaluate_design",
    "load_mission",
    "mission_from_dict",
    "optimize_designs",
    "orbital_period_s",
    "pareto_front",
    "propagate_two_body",
    "relative_energy_drift",
    "run_oak_benchmarks",
    "select_atlas_slice",
    "semimajor_axis_m",
    "simulate_mission",
    "specific_angular_momentum",
    "specific_energy",
    "velocity_verlet_step",
]

__version__ = "0.1.0"
