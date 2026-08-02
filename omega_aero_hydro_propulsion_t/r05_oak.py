from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from .architecture_compiler import PropulsionMissionIntent, compile_propulsion_architectures
from .evidence_ladder import EvidenceReceipt, assess_evidence_ladder, assess_receipt, computational_receipts
from .models import OperatingPoint, default_air, default_water, demo_rotor
from .r04_oak import run_r04_benchmarks
from .wake_graph import WakeConfig, analyze_wake_graph, induced_velocity_from_segment


@dataclass(frozen=True)
class R05OAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R05OAKReport:
    passed: bool
    status: str
    model_class: str
    gates: tuple[R05OAKGate, ...]
    physics_certified: bool = False
    certification_notice: str = (
        "R0.5 certifies deterministic software invariants only; prescribed wake, architecture "
        "ranking and evidence classification are not CFD, experiment or regulatory certification"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "model_class": self.model_class,
            "gates": [item.to_dict() for item in self.gates],
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def demo_air_intent() -> PropulsionMissionIntent:
    return PropulsionMissionIntent(
        mission_id="r05-air-demo",
        required_thrust_n=320.0,
        cruise_velocity_mps=38.0,
        installation_area_m2=1.4,
        redundancy_priority=0.35,
        efficiency_priority=0.95,
        acoustic_priority=0.65,
        compactness_priority=0.55,
        maintainability_priority=0.55,
        vectoring_priority=0.15,
    )


def demo_water_intent() -> PropulsionMissionIntent:
    return PropulsionMissionIntent(
        mission_id="r05-water-demo",
        required_thrust_n=1_800.0,
        cruise_velocity_mps=11.0,
        installation_area_m2=2.0,
        redundancy_priority=0.30,
        efficiency_priority=0.85,
        acoustic_priority=0.55,
        compactness_priority=0.45,
        maintainability_priority=0.45,
        cavitation_priority=0.80,
        vectoring_priority=0.20,
    )


def run_r05_benchmarks() -> R05OAKReport:
    design = demo_rotor()
    air = default_air()
    operating = OperatingPoint(freestream_velocity=22.0, rpm=2_200.0, collective_pitch_deg=0.0)
    config = WakeConfig(revolutions=1.0, segments_per_revolution=16)
    wake = analyze_wake_graph(design, air, operating, config=config)
    expected_segments = len(wake.bem.sections) * design.blade_count * config.step_count

    stationary = analyze_wake_graph(
        design,
        air,
        OperatingPoint(freestream_velocity=10.0, rpm=0.0),
        config=config,
    )
    segment_probe = wake.segments[0]
    regularized = induced_velocity_from_segment(segment_probe.start, segment_probe)

    air_report = compile_propulsion_architectures(demo_air_intent(), air)
    water_report = compile_propulsion_architectures(demo_water_intent(), default_water())
    ladder = assess_evidence_ladder(computational_receipts(wake_hash=wake.evidence_hash))
    phantom_cfd = EvidenceReceipt(
        receipt_id="phantom-cfd",
        tier="F4_HIGH_FIDELITY_NUMERICAL",
        artifact_sha256="0" * 64,
        provenance="synthetic negative control",
        method="unverified external solver claim",
        limitations=("no mesh study or residual convergence",),
        metadata={
            "solver": "unknown",
            "governing_equations": "unspecified",
            "boundary_conditions": "unspecified",
            "mesh_levels": 1,
            "residual_converged": False,
        },
    )
    phantom_assessment = assess_receipt(phantom_cfd)
    r04 = run_r04_benchmarks()

    gates = (
        R05OAKGate(
            "r04-regression-retained",
            r04.passed and r04.physics_certified is False,
            f"status={r04.status}",
        ),
        R05OAKGate(
            "wake-segment-cardinality",
            len(wake.segments) == expected_segments and wake.filament_count == len(wake.bem.sections) * design.blade_count,
            f"segments={len(wake.segments)}, expected={expected_segments}, filaments={wake.filament_count}",
        ),
        R05OAKGate(
            "wake-finite-and-hashed",
            wake.finite and len(wake.evidence_hash) == 64 and all(isfinite(item.speed) for item in wake.probes),
            f"finite={wake.finite}, hash={wake.evidence_hash[:16]}, vmax={wake.maximum_probe_speed:.6g}",
        ),
        R05OAKGate(
            "stationary-wake-empty",
            not stationary.segments and stationary.maximum_probe_speed == 0.0,
            f"segments={len(stationary.segments)}, vmax={stationary.maximum_probe_speed}",
        ),
        R05OAKGate(
            "vortex-core-singularity-guard",
            regularized.norm == 0.0,
            f"velocity_at_endpoint={regularized.to_dict()}",
        ),
        R05OAKGate(
            "air-architecture-domain-gate",
            air_report.best is not None
            and all(item.architecture.domain == "air" for item in air_report.candidates if item.eligible),
            f"best={None if air_report.best is None else air_report.best.architecture.architecture_id}",
        ),
        R05OAKGate(
            "water-architecture-domain-gate",
            water_report.best is not None
            and all(item.architecture.domain == "water" for item in water_report.candidates if item.eligible),
            f"best={None if water_report.best is None else water_report.best.architecture.architecture_id}",
        ),
        R05OAKGate(
            "evidence-ladder-contiguous-through-f3",
            ladder.contiguous_tier == "F3_VORTEX_PROXY" and ladder.highest_supported_tier == "F3_VORTEX_PROXY",
            f"contiguous={ladder.contiguous_tier}, highest={ladder.highest_supported_tier}",
        ),
        R05OAKGate(
            "phantom-cfd-blocked",
            not phantom_assessment.accepted
            and "mesh_independence_requires_at_least_three_levels" in phantom_assessment.blockers,
            f"blockers={phantom_assessment.blockers}",
        ),
        R05OAKGate(
            "not-physics-certified",
            wake.physics_certified is False
            and air_report.physics_certified is False
            and water_report.physics_certified is False
            and ladder.physics_certified is False
            and ladder.certification_claim is False,
            "all R0.5 artifacts remain computational research evidence",
        ),
    )
    passed = all(item.passed for item in gates)
    return R05OAKReport(
        passed=passed,
        status=(
            "CERTIFIED_COMPUTATIONAL_WAKE_ARCHITECTURE_EVIDENCE_R0_5"
            if passed
            else "FAILED_COMPUTATIONAL_WAKE_ARCHITECTURE_EVIDENCE_R0_5"
        ),
        model_class="prescribed-wake-architecture-compiler-evidence-ladder",
        gates=gates,
    )
