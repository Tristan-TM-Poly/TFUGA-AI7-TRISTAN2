from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .models import FluidMedium


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PropulsionMissionIntent:
    mission_id: str
    required_thrust_n: float
    cruise_velocity_mps: float
    installation_area_m2: float
    redundancy_priority: float = 0.5
    efficiency_priority: float = 0.8
    acoustic_priority: float = 0.5
    compactness_priority: float = 0.5
    maintainability_priority: float = 0.5
    cavitation_priority: float = 0.0
    vectoring_priority: float = 0.0

    def validate(self) -> None:
        if not self.mission_id.strip():
            raise ValueError("mission_id cannot be empty")
        if self.required_thrust_n <= 0 or self.cruise_velocity_mps < 0 or self.installation_area_m2 <= 0:
            raise ValueError("mission thrust and installation area must be positive; velocity cannot be negative")
        for name in (
            "redundancy_priority",
            "efficiency_priority",
            "acoustic_priority",
            "compactness_priority",
            "maintainability_priority",
            "cavitation_priority",
            "vectoring_priority",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArchitectureTemplate:
    architecture_id: str
    domain: str
    propulsor_count: int
    ducted: bool
    contra_rotating: bool
    vectoring: bool
    baseline_efficiency: float
    baseline_acoustic: float
    baseline_compactness: float
    baseline_redundancy: float
    baseline_maintainability: float
    baseline_cavitation_resilience: float
    installation_intensity: float
    technology_readiness_note: str
    limitations: tuple[str, ...]

    def validate(self) -> None:
        if self.domain not in {"air", "water"}:
            raise ValueError("architecture domain must be air or water")
        if self.propulsor_count < 1 or self.installation_intensity <= 0:
            raise ValueError("invalid architecture count or installation intensity")
        for name in (
            "baseline_efficiency",
            "baseline_acoustic",
            "baseline_compactness",
            "baseline_redundancy",
            "baseline_maintainability",
            "baseline_cavitation_resilience",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class ArchitectureCandidate:
    mission_id: str
    architecture: ArchitectureTemplate
    eligible: bool
    score: float
    thrust_per_propulsor_n: float
    estimated_installation_area_m2: float
    metrics: dict[str, float]
    gates: tuple[str, ...]
    risks: tuple[str, ...]
    evidence_hash: str
    model: str = "mission-architecture-heuristic-compiler-r0.5"
    physics_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "architecture": self.architecture.to_dict(),
            "eligible": self.eligible,
            "score": self.score,
            "thrust_per_propulsor_n": self.thrust_per_propulsor_n,
            "estimated_installation_area_m2": self.estimated_installation_area_m2,
            "metrics": dict(self.metrics),
            "gates": list(self.gates),
            "risks": list(self.risks),
            "evidence_hash": self.evidence_hash,
            "model": self.model,
            "physics_certified": self.physics_certified,
        }


@dataclass(frozen=True)
class ArchitectureCompilationReport:
    mission: PropulsionMissionIntent
    medium_name: str
    inferred_domain: str
    candidates: tuple[ArchitectureCandidate, ...]
    ranked_eligible_ids: tuple[str, ...]
    best: ArchitectureCandidate | None
    evidence_hash: str
    permanent_total_cap: None = None
    physics_certified: bool = False
    certification_notice: str = (
        "architecture ranking is a transparent heuristic used to choose analyses; "
        "it is not performance proof, design approval or certification"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission": self.mission.to_dict(),
            "medium_name": self.medium_name,
            "inferred_domain": self.inferred_domain,
            "candidates": [item.to_dict() for item in self.candidates],
            "ranked_eligible_ids": list(self.ranked_eligible_ids),
            "best": None if self.best is None else self.best.to_dict(),
            "evidence_hash": self.evidence_hash,
            "permanent_total_cap": self.permanent_total_cap,
            "physics_certified": self.physics_certified,
            "certification_notice": self.certification_notice,
        }


def default_architecture_templates() -> tuple[ArchitectureTemplate, ...]:
    common = ("requires geometry, powertrain, controls, structure and mission-specific validation",)
    return (
        ArchitectureTemplate(
            "air-open-propeller",
            "air",
            1,
            False,
            False,
            False,
            0.88,
            0.54,
            0.70,
            0.25,
            0.88,
            1.00,
            0.70,
            "mature architecture; installation and blade design remain mission-specific",
            common + ("exposed tip-vortex and acoustic constraints",),
        ),
        ArchitectureTemplate(
            "air-ducted-fan",
            "air",
            1,
            True,
            False,
            False,
            0.76,
            0.74,
            0.82,
            0.30,
            0.62,
            1.00,
            0.88,
            "mature in bounded regimes; duct losses and off-design behavior matter",
            common + ("duct mass, inlet distortion and stall margin are not represented",),
        ),
        ArchitectureTemplate(
            "air-distributed-electric",
            "air",
            8,
            False,
            False,
            True,
            0.80,
            0.68,
            0.48,
            0.92,
            0.45,
            1.00,
            1.65,
            "research and emerging operational architectures; integration dominates",
            common + ("power distribution, thermal management and coupled control are not represented",),
        ),
        ArchitectureTemplate(
            "air-contra-rotating",
            "air",
            2,
            False,
            True,
            False,
            0.91,
            0.42,
            0.72,
            0.45,
            0.38,
            1.00,
            0.95,
            "established physical concept with complex aeroacoustic and mechanical integration",
            common + ("rotor-rotor interaction and tonal noise require higher-fidelity evidence",),
        ),
        ArchitectureTemplate(
            "air-boundary-layer-ingesting-fan",
            "air",
            1,
            True,
            False,
            False,
            0.93,
            0.66,
            0.86,
            0.25,
            0.32,
            1.00,
            1.10,
            "advanced integration hypothesis whose benefit depends on full vehicle coupling",
            common + ("distortion tolerance and vehicle-level bookkeeping are mandatory",),
        ),
        ArchitectureTemplate(
            "water-open-propeller",
            "water",
            1,
            False,
            False,
            False,
            0.88,
            0.50,
            0.72,
            0.25,
            0.86,
            0.54,
            0.72,
            "mature architecture; cavitation and hull wake are mission-specific",
            common + ("cavitation erosion, free-surface and hull interaction are not represented",),
        ),
        ArchitectureTemplate(
            "water-ducted-propeller",
            "water",
            1,
            True,
            False,
            False,
            0.80,
            0.67,
            0.78,
            0.30,
            0.58,
            0.76,
            0.90,
            "mature for selected loading regimes; nozzle shape and gap losses dominate",
            common + ("duct-rotor interaction and debris tolerance are not represented",),
        ),
        ArchitectureTemplate(
            "water-contra-rotating",
            "water",
            2,
            False,
            True,
            False,
            0.92,
            0.43,
            0.70,
            0.48,
            0.36,
            0.66,
            0.98,
            "established concept with demanding shafting, sealing and interaction physics",
            common + ("contra-rotating cavitation and mechanical complexity require testing",),
        ),
        ArchitectureTemplate(
            "water-waterjet",
            "water",
            1,
            True,
            False,
            True,
            0.72,
            0.75,
            0.88,
            0.30,
            0.52,
            0.84,
            1.02,
            "mature at appropriate speed and loading; intake and nozzle integration dominate",
            common + ("intake losses, ingestion and pump cavitation are not represented",),
        ),
        ArchitectureTemplate(
            "water-podded-azimuth",
            "water",
            2,
            False,
            False,
            True,
            0.82,
            0.60,
            0.62,
            0.72,
            0.66,
            0.62,
            1.28,
            "mature marine architecture with strong maneuvering benefits",
            common + ("pod drag, sealing, electrical losses and structural loads are not represented",),
        ),
    )


def infer_domain(medium: FluidMedium) -> str:
    medium.validate()
    return "water" if medium.vapor_pressure is not None or medium.density > 100.0 else "air"


def _weights(mission: PropulsionMissionIntent) -> dict[str, float]:
    raw = {
        "efficiency": mission.efficiency_priority,
        "acoustic": mission.acoustic_priority,
        "compactness": mission.compactness_priority,
        "redundancy": mission.redundancy_priority,
        "maintainability": mission.maintainability_priority,
        "cavitation": mission.cavitation_priority,
        "vectoring": mission.vectoring_priority,
    }
    total = sum(raw.values())
    if total <= 1e-15:
        return {key: 1.0 / len(raw) for key in raw}
    return {key: value / total for key, value in raw.items()}


def compile_propulsion_architectures(
    mission: PropulsionMissionIntent,
    medium: FluidMedium,
    *,
    templates: Iterable[ArchitectureTemplate] | None = None,
) -> ArchitectureCompilationReport:
    mission.validate()
    medium.validate()
    domain = infer_domain(medium)
    weights = _weights(mission)
    candidates: list[ArchitectureCandidate] = []
    for template in templates or default_architecture_templates():
        template.validate()
        area = template.installation_intensity * mission.required_thrust_n / 2_500.0
        thrust_per_propulsor = mission.required_thrust_n / template.propulsor_count
        gates: list[str] = []
        risks = list(template.limitations)
        if template.domain != domain:
            gates.append("domain_mismatch")
        if area > mission.installation_area_m2:
            gates.append("installation_area_proxy")
        if mission.redundancy_priority >= 0.75 and template.propulsor_count < 2:
            gates.append("redundancy_priority")
        if mission.vectoring_priority >= 0.75 and not template.vectoring:
            gates.append("vectoring_priority")
        if domain == "water" and mission.cavitation_priority >= 0.70 and template.baseline_cavitation_resilience < 0.65:
            gates.append("cavitation_priority")

        metrics = {
            "efficiency": template.baseline_efficiency,
            "acoustic": template.baseline_acoustic,
            "compactness": template.baseline_compactness,
            "redundancy": template.baseline_redundancy,
            "maintainability": template.baseline_maintainability,
            "cavitation": template.baseline_cavitation_resilience if domain == "water" else 1.0,
            "vectoring": 1.0 if template.vectoring else 0.0,
        }
        score = sum(weights[key] * metrics[key] for key in weights)
        score -= 0.18 * len(gates)
        score -= 0.04 * max(0.0, area / mission.installation_area_m2 - 1.0)
        eligible = not gates
        stable = {
            "mission": mission.to_dict(),
            "medium": medium.to_dict(),
            "template": template.to_dict(),
            "metrics": metrics,
            "gates": gates,
            "score": score,
        }
        candidates.append(
            ArchitectureCandidate(
                mission_id=mission.mission_id,
                architecture=template,
                eligible=eligible,
                score=score,
                thrust_per_propulsor_n=thrust_per_propulsor,
                estimated_installation_area_m2=area,
                metrics=metrics,
                gates=tuple(gates),
                risks=tuple(risks),
                evidence_hash=_digest(stable),
            )
        )
    ranked = tuple(sorted((item for item in candidates if item.eligible), key=lambda item: (-item.score, item.architecture.architecture_id)))
    stable_report = {
        "mission": mission.to_dict(),
        "medium": medium.to_dict(),
        "domain": domain,
        "candidate_hashes": [item.evidence_hash for item in candidates],
        "ranked": [item.architecture.architecture_id for item in ranked],
    }
    return ArchitectureCompilationReport(
        mission=mission,
        medium_name=medium.name,
        inferred_domain=domain,
        candidates=tuple(candidates),
        ranked_eligible_ids=tuple(item.architecture.architecture_id for item in ranked),
        best=ranked[0] if ranked else None,
        evidence_hash=_digest(stable_report),
    )
