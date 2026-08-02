from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import cos, isfinite, pi, sin, sqrt
from typing import Any, Iterable

from .annular_bem import AnnularBEMAnalysis, analyze_annular_bem
from .models import FluidMedium, OperatingPoint, RotorDesign
from .polars import PolarRegistry


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Vector3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: "Vector3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3") -> "Vector3":
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @property
    def norm(self) -> float:
        return sqrt(self.dot(self))

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


ZERO_VECTOR = Vector3(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class WakeConfig:
    revolutions: float = 2.0
    segments_per_revolution: int = 24
    core_radius_fraction: float = 0.015
    contraction_ratio: float = 0.10
    minimum_convection_fraction: float = 0.02
    probe_axial_diameters: tuple[float, ...] = (0.25, 0.50, 1.00, 2.00)

    def validate(self) -> None:
        if self.revolutions <= 0:
            raise ValueError("revolutions must be positive")
        if self.segments_per_revolution < 8:
            raise ValueError("segments_per_revolution must be at least eight")
        if not 0.0 < self.core_radius_fraction <= 0.20:
            raise ValueError("core_radius_fraction must lie in (0, 0.20]")
        if not 0.0 <= self.contraction_ratio < 0.50:
            raise ValueError("contraction_ratio must lie in [0, 0.50)")
        if not 0.0 < self.minimum_convection_fraction <= 0.25:
            raise ValueError("minimum_convection_fraction must lie in (0, 0.25]")
        if not self.probe_axial_diameters or any(value < 0 for value in self.probe_axial_diameters):
            raise ValueError("probe locations must be non-negative")

    @property
    def step_count(self) -> int:
        return max(1, round(self.revolutions * self.segments_per_revolution))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["probe_axial_diameters"] = list(self.probe_axial_diameters)
        payload["step_count"] = self.step_count
        return payload


@dataclass(frozen=True)
class WakeNode:
    filament_id: str
    node_index: int
    position: Vector3

    def to_dict(self) -> dict[str, Any]:
        return {
            "filament_id": self.filament_id,
            "node_index": self.node_index,
            "position": self.position.to_dict(),
        }


@dataclass(frozen=True)
class VortexSegment:
    filament_id: str
    segment_index: int
    blade_index: int
    source_radius: float
    circulation: float
    core_radius: float
    start: Vector3
    end: Vector3

    @property
    def length(self) -> float:
        return (self.end - self.start).norm

    def to_dict(self) -> dict[str, Any]:
        return {
            "filament_id": self.filament_id,
            "segment_index": self.segment_index,
            "blade_index": self.blade_index,
            "source_radius": self.source_radius,
            "circulation": self.circulation,
            "core_radius": self.core_radius,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "length": self.length,
        }


@dataclass(frozen=True)
class WakeProbe:
    axial_diameters: float
    position: Vector3
    induced_velocity: Vector3

    @property
    def speed(self) -> float:
        return self.induced_velocity.norm

    @property
    def crossflow_speed(self) -> float:
        return sqrt(self.induced_velocity.y**2 + self.induced_velocity.z**2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "axial_diameters": self.axial_diameters,
            "position": self.position.to_dict(),
            "induced_velocity": self.induced_velocity.to_dict(),
            "speed": self.speed,
            "crossflow_speed": self.crossflow_speed,
        }


@dataclass(frozen=True)
class WakeGraphReport:
    design_name: str
    medium_name: str
    operating_point: OperatingPoint
    config: WakeConfig
    bem: AnnularBEMAnalysis
    nodes: tuple[WakeNode, ...]
    segments: tuple[VortexSegment, ...]
    probes: tuple[WakeProbe, ...]
    filament_count: int
    total_segment_length: float
    circulation_l1: float
    maximum_probe_speed: float
    finite: bool
    evidence_hash: str
    model: str = "regularized-helical-vortex-proxy-r0.5"
    physical_fidelity_claim: bool = False
    physics_certified: bool = False
    limitations: tuple[str, ...] = (
        "prescribed helical wake; no free-wake relaxation",
        "circulation inferred from low-order blade-element sections",
        "no viscous wake diffusion beyond a fixed numerical core",
        "no unsteady blade-vortex interaction or turbulence model",
        "not CFD, FSI, experiment, airworthiness or seaworthiness evidence",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_name": self.design_name,
            "medium_name": self.medium_name,
            "operating_point": self.operating_point.to_dict(),
            "config": self.config.to_dict(),
            "bem": self.bem.to_dict(),
            "nodes": [item.to_dict() for item in self.nodes],
            "segments": [item.to_dict() for item in self.segments],
            "probes": [item.to_dict() for item in self.probes],
            "filament_count": self.filament_count,
            "total_segment_length": self.total_segment_length,
            "circulation_l1": self.circulation_l1,
            "maximum_probe_speed": self.maximum_probe_speed,
            "finite": self.finite,
            "evidence_hash": self.evidence_hash,
            "model": self.model,
            "physical_fidelity_claim": self.physical_fidelity_claim,
            "physics_certified": self.physics_certified,
            "limitations": list(self.limitations),
        }


def induced_velocity_from_segment(point: Vector3, segment: VortexSegment) -> Vector3:
    """Regularized finite-segment Biot-Savart velocity.

    The core radius prevents a numerical singularity. This is a deterministic
    vortex-method primitive, not a turbulence or viscous-flow solution.
    """
    r1 = point - segment.start
    r2 = point - segment.end
    r0 = segment.end - segment.start
    r1_norm = r1.norm
    r2_norm = r2.norm
    r0_norm = r0.norm
    if r1_norm <= 1e-15 or r2_norm <= 1e-15 or r0_norm <= 1e-15 or abs(segment.circulation) <= 1e-18:
        return ZERO_VECTOR
    cross = r1.cross(r2)
    cross_sq = cross.dot(cross)
    regularizer = (segment.core_radius * r0_norm) ** 2
    denominator = 4.0 * pi * (cross_sq + regularizer)
    if denominator <= 1e-30:
        return ZERO_VECTOR
    directional = r0.dot(r1 * (1.0 / r1_norm) - r2 * (1.0 / r2_norm))
    return cross * (segment.circulation * directional / denominator)


def induced_velocity(point: Vector3, segments: Iterable[VortexSegment]) -> Vector3:
    total = ZERO_VECTOR
    for segment in segments:
        total = total + induced_velocity_from_segment(point, segment)
    return total


def _circulation_proxy(section: Any) -> float:
    return 0.5 * section.lift_coefficient * section.relative_speed * section.chord


def analyze_wake_graph(
    design: RotorDesign,
    medium: FluidMedium,
    operating: OperatingPoint,
    *,
    config: WakeConfig | None = None,
    registry: PolarRegistry | None = None,
) -> WakeGraphReport:
    design.validate()
    medium.validate()
    operating.validate()
    cfg = config or WakeConfig()
    cfg.validate()
    bem = analyze_annular_bem(design, medium, operating, registry=registry)

    nodes: list[WakeNode] = []
    segments: list[VortexSegment] = []
    omega = operating.rpm * 2.0 * pi / 60.0
    if omega > 1e-15:
        core_radius = cfg.core_radius_fraction * design.tip_radius
        total_angle = 2.0 * pi * cfg.revolutions
        for section_index, section in enumerate(bem.sections):
            gamma = _circulation_proxy(section)
            throughflow = abs(operating.freestream_velocity + section.axial_induced_velocity)
            minimum = cfg.minimum_convection_fraction * omega * design.tip_radius
            convection = max(throughflow, minimum)
            axial_per_radian = convection / omega
            for blade_index in range(design.blade_count):
                filament_id = f"s{section_index:03d}-b{blade_index:03d}"
                phase = 2.0 * pi * blade_index / design.blade_count
                filament_nodes: list[WakeNode] = []
                for node_index in range(cfg.step_count + 1):
                    fraction = node_index / cfg.step_count
                    angle = total_angle * fraction
                    radius = section.radius * (1.0 - cfg.contraction_ratio * fraction)
                    position = Vector3(
                        axial_per_radian * angle,
                        radius * cos(phase + angle),
                        radius * sin(phase + angle),
                    )
                    node = WakeNode(filament_id, node_index, position)
                    nodes.append(node)
                    filament_nodes.append(node)
                for segment_index, (left, right) in enumerate(zip(filament_nodes, filament_nodes[1:])):
                    segments.append(
                        VortexSegment(
                            filament_id=filament_id,
                            segment_index=segment_index,
                            blade_index=blade_index,
                            source_radius=section.radius,
                            circulation=gamma,
                            core_radius=core_radius,
                            start=left.position,
                            end=right.position,
                        )
                    )

    probes = tuple(
        WakeProbe(
            axial_diameters=value,
            position=Vector3(value * design.diameter, 0.0, 0.0),
            induced_velocity=induced_velocity(Vector3(value * design.diameter, 0.0, 0.0), segments),
        )
        for value in cfg.probe_axial_diameters
    )
    finite = all(
        isfinite(value)
        for segment in segments
        for value in (
            segment.start.x,
            segment.start.y,
            segment.start.z,
            segment.end.x,
            segment.end.y,
            segment.end.z,
            segment.circulation,
            segment.length,
        )
    ) and all(
        isfinite(value)
        for probe in probes
        for value in (
            probe.induced_velocity.x,
            probe.induced_velocity.y,
            probe.induced_velocity.z,
            probe.speed,
        )
    )
    stable = {
        "design": design.to_dict(),
        "medium": medium.to_dict(),
        "operating": operating.to_dict(),
        "config": cfg.to_dict(),
        "bem_hash_material": {
            "thrust": bem.thrust,
            "torque": bem.torque,
            "sections": [
                {
                    "radius": item.radius,
                    "cl": item.lift_coefficient,
                    "relative_speed": item.relative_speed,
                    "axial_induced_velocity": item.axial_induced_velocity,
                }
                for item in bem.sections
            ],
        },
        "segment_count": len(segments),
        "segment_hashes": [_digest(item.to_dict()) for item in segments],
        "probes": [item.to_dict() for item in probes],
    }
    return WakeGraphReport(
        design_name=design.name,
        medium_name=medium.name,
        operating_point=operating,
        config=cfg,
        bem=bem,
        nodes=tuple(nodes),
        segments=tuple(segments),
        probes=probes,
        filament_count=len(bem.sections) * design.blade_count if segments else 0,
        total_segment_length=sum(item.length for item in segments),
        circulation_l1=sum(abs(item.circulation) for item in segments),
        maximum_probe_speed=max((item.speed for item in probes), default=0.0),
        finite=finite,
        evidence_hash=_digest(stable),
    )
