"""Ω-RIGID-BODY-T R0.2: analytic, geometric, forced and atlas rigid-body lab."""
from .analytic import ExactParameters, exact_omega, exact_parameters_from_state, near_separatrix_period, separatrix_omega
from .atlas import AtlasCell, AtlasConfig, atlas_manifest, default_atlas_config, iter_atlas, stroboscopic_map
from .geometry import (
    PhaseClosureReport,
    herpolhode_points,
    montgomery_phase,
    oriented_solid_angle_closed_polygon,
    phase_closure_report,
    polhode_points,
)
from .integrators import MidpointTrajectory, Trajectory, integrate_midpoint_torque_free, midpoint_step, simulate_adaptive
from .model import BalanceReport, Invariants, PrincipalMoments, StabilityMode, euler_rhs, invariants, principal_axis_stability
from .oak import BenchmarkResult, OAKReport, run_oak_benchmarks

__all__ = [
    "AtlasCell",
    "AtlasConfig",
    "BalanceReport",
    "BenchmarkResult",
    "ExactParameters",
    "Invariants",
    "MidpointTrajectory",
    "OAKReport",
    "PhaseClosureReport",
    "PrincipalMoments",
    "StabilityMode",
    "Trajectory",
    "atlas_manifest",
    "default_atlas_config",
    "euler_rhs",
    "exact_omega",
    "exact_parameters_from_state",
    "herpolhode_points",
    "integrate_midpoint_torque_free",
    "invariants",
    "iter_atlas",
    "midpoint_step",
    "montgomery_phase",
    "near_separatrix_period",
    "oriented_solid_angle_closed_polygon",
    "phase_closure_report",
    "polhode_points",
    "principal_axis_stability",
    "run_oak_benchmarks",
    "separatrix_omega",
    "simulate_adaptive",
    "stroboscopic_map",
]

__version__ = "0.2.0"
