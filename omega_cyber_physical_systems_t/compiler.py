from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .models import DOMAINS


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


MOTION_TYPES = (
    "none",
    "linear",
    "rotary",
    "mobile",
    "fluid",
    "multi_axis",
    "deformable",
    "propulsive",
)


@dataclass(frozen=True)
class PrototypeIntent:
    intent_id: str
    name: str
    required_domains: tuple[str, ...]
    motion_type: str
    continuous_power_w: float
    peak_power_w: float
    supply_voltage_v: float
    installation_volume_m3: float
    payload_or_load: float
    precision_priority: float = 0.5
    efficiency_priority: float = 0.5
    safety_priority: float = 0.5
    maintainability_priority: float = 0.5
    modularity_priority: float = 0.5
    redundancy_priority: float = 0.0
    environment: str = "laboratory"

    def validate(self) -> None:
        if not self.intent_id.strip() or not self.name.strip() or not self.environment.strip():
            raise ValueError("intent identifiers, name and environment are required")
        if not self.required_domains:
            raise ValueError("required_domains cannot be empty")
        if len(set(self.required_domains)) != len(self.required_domains):
            raise ValueError("required_domains must be unique")
        if any(domain not in DOMAINS for domain in self.required_domains):
            raise ValueError("intent contains an unknown domain")
        if self.motion_type not in MOTION_TYPES:
            raise ValueError("unknown motion_type")
        if min(
            self.continuous_power_w,
            self.peak_power_w,
            self.supply_voltage_v,
            self.installation_volume_m3,
            self.payload_or_load,
        ) < 0:
            raise ValueError("power, voltage, volume and load cannot be negative")
        if self.peak_power_w < self.continuous_power_w:
            raise ValueError("peak_power_w must be at least continuous_power_w")
        for name in (
            "precision_priority",
            "efficiency_priority",
            "safety_priority",
            "maintainability_priority",
            "modularity_priority",
            "redundancy_priority",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["required_domains"] = list(self.required_domains)
        return payload


@dataclass(frozen=True)
class PrototypeArchitecture:
    architecture_id: str
    name: str
    supported_domains: tuple[str, ...]
    motion_types: tuple[str, ...]
    component_kinds: tuple[str, ...]
    minimum_volume_m3: float
    voltage_min_v: float
    voltage_max_v: float
    continuous_power_limit_w: float
    peak_power_limit_w: float
    precision_capability: float
    efficiency_capability: float
    safety_capability: float
    maintainability_capability: float
    modularity_capability: float
    redundancy_capability: float
    complexity: float
    evidence_plan: tuple[str, ...]

    def validate(self) -> None:
        if not self.architecture_id.strip() or not self.name.strip():
            raise ValueError("architecture ID and name are required")
        if any(domain not in DOMAINS for domain in self.supported_domains):
            raise ValueError("architecture contains an unknown domain")
        if any(item not in MOTION_TYPES for item in self.motion_types):
            raise ValueError("architecture contains an unknown motion type")
        if not self.component_kinds or len(set(self.component_kinds)) != len(self.component_kinds):
            raise ValueError("component_kinds must be non-empty and unique")
        if self.minimum_volume_m3 < 0 or self.voltage_min_v < 0 or self.voltage_max_v <= self.voltage_min_v:
            raise ValueError("architecture volume or voltage range is invalid")
        if self.continuous_power_limit_w < 0 or self.peak_power_limit_w < self.continuous_power_limit_w:
            raise ValueError("architecture power envelope is invalid")
        for name in (
            "precision_capability",
            "efficiency_capability",
            "safety_capability",
            "maintainability_capability",
            "modularity_capability",
            "redundancy_capability",
            "complexity",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if not self.evidence_plan:
            raise ValueError("architecture evidence_plan cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["supported_domains"] = list(self.supported_domains)
        payload["motion_types"] = list(self.motion_types)
        payload["component_kinds"] = list(self.component_kinds)
        payload["evidence_plan"] = list(self.evidence_plan)
        return payload


@dataclass(frozen=True)
class PrototypeCandidate:
    architecture: PrototypeArchitecture
    eligible: bool
    score: float
    domain_coverage: float
    blockers: tuple[str, ...]
    strengths: tuple[str, ...]
    next_evidence: tuple[str, ...]
    candidate_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture": self.architecture.to_dict(),
            "eligible": self.eligible,
            "score": self.score,
            "domain_coverage": self.domain_coverage,
            "blockers": list(self.blockers),
            "strengths": list(self.strengths),
            "next_evidence": list(self.next_evidence),
            "candidate_hash": self.candidate_hash,
        }


@dataclass(frozen=True)
class PrototypeCompilationReport:
    intent: PrototypeIntent
    candidates: tuple[PrototypeCandidate, ...]
    best: PrototypeCandidate | None
    eligible_count: int
    evidence_hash: str
    permanent_total_cap: None = None
    heuristic_only: bool = True
    physics_certified: bool = False
    engineering_recommendation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_dict(),
            "candidates": [item.to_dict() for item in self.candidates],
            "best": None if self.best is None else self.best.to_dict(),
            "eligible_count": self.eligible_count,
            "evidence_hash": self.evidence_hash,
            "permanent_total_cap": self.permanent_total_cap,
            "heuristic_only": self.heuristic_only,
            "physics_certified": self.physics_certified,
            "engineering_recommendation": self.engineering_recommendation,
            "limitations": [
                "architecture scores are transparent routing heuristics",
                "component sizing, CAD, FEA, CFD, EMC, safety and manufacturing remain separate",
                "the best candidate is not automatically the best physical design",
            ],
        }


def default_prototype_architectures() -> tuple[PrototypeArchitecture, ...]:
    common_evidence = (
        "D0_STRUCTURE: interface-complete blueprint",
        "D1_UNIT_TESTED: deterministic component tests",
        "D2_SIMULATED_COMPONENT: parameterized component models",
        "D3_COSIMULATED_SYSTEM: coupled energy and timing simulation",
    )
    return (
        PrototypeArchitecture(
            "servo-linear-axis",
            "Precision electromechanical linear axis",
            ("mechanical_translational", "mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "software", "data"),
            ("linear",),
            ("power-source", "motor-drive", "electric-motor", "transmission", "linear-load", "position-sensor", "real-time-controller", "safety-interlock"),
            0.004,
            12.0,
            96.0,
            3_000.0,
            8_000.0,
            0.96,
            0.78,
            0.88,
            0.82,
            0.83,
            0.40,
            0.48,
            common_evidence + ("D5_BENCH_EXPERIMENT: calibrated positioning and thermal test",),
        ),
        PrototypeArchitecture(
            "rotary-servo-stage",
            "Direct or geared rotary servo stage",
            ("mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "software", "data"),
            ("rotary",),
            ("power-source", "inverter", "servo-motor", "gearbox-or-direct-drive", "encoder", "controller", "brake"),
            0.003,
            12.0,
            800.0,
            20_000.0,
            60_000.0,
            0.94,
            0.84,
            0.86,
            0.78,
            0.76,
            0.45,
            0.52,
            common_evidence + ("D5_BENCH_EXPERIMENT: torque-speed and brake validation",),
        ),
        PrototypeArchitecture(
            "mobile-robot-platform",
            "Multi-wheel or tracked mobile robot",
            ("mechanical_translational", "mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "software", "data"),
            ("mobile", "multi_axis"),
            ("battery", "power-distribution", "traction-drives", "motors", "wheels-or-tracks", "imu", "encoders", "compute", "safety-controller"),
            0.025,
            12.0,
            800.0,
            15_000.0,
            45_000.0,
            0.72,
            0.76,
            0.86,
            0.72,
            0.90,
            0.86,
            0.72,
            common_evidence + ("D4_HIL_SIL: navigation and emergency-stop HIL", "D6_FIELD_TRIAL: bounded supervised route"),
        ),
        PrototypeArchitecture(
            "robotic-manipulator",
            "Multi-axis robotic manipulator or gripper",
            ("mechanical_translational", "mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "software", "data"),
            ("linear", "rotary", "multi_axis", "deformable"),
            ("actuator-array", "joint-transmissions", "encoders", "force-sensors", "real-time-control", "trajectory-planner", "safety-monitor"),
            0.015,
            12.0,
            800.0,
            12_000.0,
            40_000.0,
            0.92,
            0.72,
            0.91,
            0.66,
            0.84,
            0.54,
            0.78,
            common_evidence + ("D4_HIL_SIL: collision and limit HIL", "D5_BENCH_EXPERIMENT: load and repeatability tests"),
        ),
        PrototypeArchitecture(
            "pump-valve-process-skid",
            "Instrumented pump, valve and process-fluid skid",
            ("mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "fluid", "software", "data"),
            ("fluid", "rotary"),
            ("tank", "pump", "motor-drive", "valves", "pressure-flow-temperature-sensors", "PLC", "relief-path", "containment"),
            0.08,
            24.0,
            800.0,
            50_000.0,
            150_000.0,
            0.68,
            0.80,
            0.92,
            0.86,
            0.80,
            0.62,
            0.58,
            common_evidence + ("D5_BENCH_EXPERIMENT: pressure, flow, leakage and relief testing",),
        ),
        PrototypeArchitecture(
            "battery-power-thermal-module",
            "Battery, converter, BMS and thermal-control module",
            ("electrical_power", "electronic_signal", "thermal", "fluid", "software", "data"),
            ("none", "fluid"),
            ("certified-battery-module", "contactors", "fuses", "converter", "BMS", "thermal-loop", "sensors", "supervisory-controller"),
            0.012,
            12.0,
            1_000.0,
            100_000.0,
            250_000.0,
            0.58,
            0.91,
            0.96,
            0.75,
            0.84,
            0.72,
            0.66,
            common_evidence + ("D5_BENCH_EXPERIMENT: certified low-energy module and thermal-abuse-safe protocol",),
        ),
        PrototypeArchitecture(
            "precision-gimbal-instrument",
            "Precision gimbal and sensing instrument",
            ("mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "software", "data"),
            ("rotary", "multi_axis"),
            ("gimbal-structure", "torque-motors", "encoders", "imu", "camera-or-instrument", "controller", "thermal-management"),
            0.006,
            12.0,
            120.0,
            2_500.0,
            7_500.0,
            0.98,
            0.69,
            0.82,
            0.70,
            0.78,
            0.30,
            0.63,
            common_evidence + ("D5_BENCH_EXPERIMENT: pointing, vibration and thermal drift characterization",),
        ),
        PrototypeArchitecture(
            "smart-manufacturing-cell",
            "Integrated machine or manufacturing cell",
            ("mechanical_translational", "mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "fluid", "software", "data"),
            ("linear", "rotary", "multi_axis", "fluid"),
            ("machine-frame", "motion-system", "tooling", "power-electronics", "sensors", "PLC", "safety-PLC", "HMI", "data-logger", "guarding"),
            0.5,
            24.0,
            800.0,
            250_000.0,
            600_000.0,
            0.90,
            0.76,
            0.97,
            0.84,
            0.91,
            0.68,
            0.88,
            common_evidence + ("D4_HIL_SIL: safety PLC and sequence HIL", "D7_ENGINEERING_REVIEW: machine-safety review"),
        ),
        PrototypeArchitecture(
            "autonomous-vehicle-platform",
            "Integrated autonomous ground, air or marine platform",
            ("mechanical_translational", "mechanical_rotational", "electrical_power", "electronic_signal", "thermal", "fluid", "software", "data"),
            ("mobile", "multi_axis", "propulsive"),
            ("energy-system", "propulsion-or-traction", "steering-or-vectoring", "navigation-sensors", "compute", "communications", "flight-or-motion-controller", "independent-safety-monitor"),
            0.08,
            24.0,
            1_000.0,
            300_000.0,
            900_000.0,
            0.78,
            0.88,
            0.93,
            0.62,
            0.92,
            0.90,
            0.94,
            common_evidence + ("D4_HIL_SIL: full mission and fault HIL", "D6_FIELD_TRIAL: supervised restricted-area trial", "D8_REGULATORY_CERTIFICATION: external authority only"),
        ),
        PrototypeArchitecture(
            "propulsion-module-adapter",
            "Propulsion subsystem integrated into a larger cyberphysical vehicle",
            ("mechanical_rotational", "mechanical_translational", "electrical_power", "electronic_signal", "thermal", "fluid", "software", "data"),
            ("propulsive", "fluid", "rotary"),
            ("energy-source", "converter", "motor-or-engine", "propulsor", "sensors", "controller", "thermal-system", "vehicle-interface"),
            0.02,
            12.0,
            1_000.0,
            500_000.0,
            1_500_000.0,
            0.74,
            0.92,
            0.89,
            0.68,
            0.88,
            0.72,
            0.82,
            common_evidence + ("D5_BENCH_EXPERIMENT: thrust/torque/power test", "D7_ENGINEERING_REVIEW: vehicle integration review"),
        ),
    )


def _capability_score(priority: float, capability: float) -> float:
    return priority * capability


def compile_prototype(
    intent: PrototypeIntent,
    *,
    architectures: Sequence[PrototypeArchitecture] | None = None,
) -> PrototypeCompilationReport:
    intent.validate()
    templates = tuple(architectures or default_prototype_architectures())
    if not templates:
        raise ValueError("at least one prototype architecture is required")
    candidates: list[PrototypeCandidate] = []
    required = set(intent.required_domains)
    for architecture in templates:
        architecture.validate()
        supported = set(architecture.supported_domains)
        coverage = len(required & supported) / len(required)
        blockers: list[str] = []
        if not required.issubset(supported):
            blockers.append("missing_required_domains")
        if intent.motion_type not in architecture.motion_types:
            blockers.append("motion_type_not_supported")
        if intent.installation_volume_m3 < architecture.minimum_volume_m3:
            blockers.append("installation_volume_too_small")
        if not architecture.voltage_min_v <= intent.supply_voltage_v <= architecture.voltage_max_v:
            blockers.append("supply_voltage_outside_template_range")
        if intent.continuous_power_w > architecture.continuous_power_limit_w:
            blockers.append("continuous_power_exceeds_template")
        if intent.peak_power_w > architecture.peak_power_limit_w:
            blockers.append("peak_power_exceeds_template")
        eligible = not blockers
        weighted = (
            _capability_score(intent.precision_priority, architecture.precision_capability)
            + _capability_score(intent.efficiency_priority, architecture.efficiency_capability)
            + _capability_score(intent.safety_priority, architecture.safety_capability)
            + _capability_score(intent.maintainability_priority, architecture.maintainability_capability)
            + _capability_score(intent.modularity_priority, architecture.modularity_capability)
            + _capability_score(intent.redundancy_priority, architecture.redundancy_capability)
        )
        total_priority = (
            intent.precision_priority
            + intent.efficiency_priority
            + intent.safety_priority
            + intent.maintainability_priority
            + intent.modularity_priority
            + intent.redundancy_priority
        )
        capability = weighted / max(total_priority, 1e-12)
        headroom = min(
            1.0,
            architecture.continuous_power_limit_w / max(intent.continuous_power_w, 1.0),
            architecture.peak_power_limit_w / max(intent.peak_power_w, 1.0),
        )
        volume_fit = min(1.0, intent.installation_volume_m3 / max(architecture.minimum_volume_m3, 1e-12))
        score = (
            0.42 * coverage
            + 0.32 * capability
            + 0.12 * headroom
            + 0.08 * volume_fit
            + 0.06 * (1.0 - architecture.complexity)
            - 0.20 * len(blockers)
        )
        strengths: list[str] = []
        for name, capability_value, priority in (
            ("precision", architecture.precision_capability, intent.precision_priority),
            ("efficiency", architecture.efficiency_capability, intent.efficiency_priority),
            ("safety", architecture.safety_capability, intent.safety_priority),
            ("maintainability", architecture.maintainability_capability, intent.maintainability_priority),
            ("modularity", architecture.modularity_capability, intent.modularity_priority),
            ("redundancy", architecture.redundancy_capability, intent.redundancy_priority),
        ):
            if priority >= 0.6 and capability_value >= 0.8:
                strengths.append(name)
        payload = {
            "intent": intent.to_dict(),
            "architecture": architecture.to_dict(),
            "eligible": eligible,
            "score": score,
            "blockers": blockers,
        }
        candidates.append(
            PrototypeCandidate(
                architecture=architecture,
                eligible=eligible,
                score=score,
                domain_coverage=coverage,
                blockers=tuple(blockers),
                strengths=tuple(strengths),
                next_evidence=architecture.evidence_plan,
                candidate_hash=_stable_hash(payload),
            )
        )
    ordered = tuple(sorted(candidates, key=lambda item: (-int(item.eligible), -item.score, item.architecture.architecture_id)))
    eligible_candidates = [item for item in ordered if item.eligible]
    best = eligible_candidates[0] if eligible_candidates else None
    payload = {
        "intent": intent.to_dict(),
        "candidates": [item.to_dict() for item in ordered],
        "best": None if best is None else best.architecture.architecture_id,
    }
    return PrototypeCompilationReport(
        intent=intent,
        candidates=ordered,
        best=best,
        eligible_count=len(eligible_candidates),
        evidence_hash=_stable_hash(payload),
    )


def demo_integrated_robot_intent() -> PrototypeIntent:
    return PrototypeIntent(
        intent_id="omega-cps-integrated-robot",
        name="Integrated mobile manipulation research platform",
        required_domains=(
            "mechanical_translational",
            "mechanical_rotational",
            "electrical_power",
            "electronic_signal",
            "thermal",
            "software",
            "data",
        ),
        motion_type="mobile",
        continuous_power_w=1_500.0,
        peak_power_w=4_000.0,
        supply_voltage_v=48.0,
        installation_volume_m3=0.18,
        payload_or_load=35.0,
        precision_priority=0.65,
        efficiency_priority=0.75,
        safety_priority=0.95,
        maintainability_priority=0.80,
        modularity_priority=0.95,
        redundancy_priority=0.75,
        environment="indoor-supervised-research",
    )
