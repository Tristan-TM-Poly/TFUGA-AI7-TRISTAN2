from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Mapping


@dataclass(frozen=True)
class ScienceQuestion:
    question_id: str
    statement: str
    hypothesis_ids: tuple[str, ...]
    required_discrimination: float = 0.5


@dataclass(frozen=True)
class Observable:
    observable_id: str
    name: str
    modality: str
    required_sensitivity: float = 0.0
    required_resolution: float = 0.0
    expected_discrimination: float = 0.0


@dataclass(frozen=True)
class SensorCapability:
    sensor_id: str
    observables: tuple[str, ...]
    sensitivity: float
    resolution: float
    calibration_confidence: float
    resource_cost: float = 0.0
    risk: float = 0.0
    failure_modes: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def supports(self, observable: Observable) -> bool:
        return (
            observable.observable_id in self.observables
            and self.sensitivity >= observable.required_sensitivity
            and self.resolution >= observable.required_resolution
            and self.calibration_confidence > 0.0
        )


@dataclass(frozen=True)
class DetectorGenome:
    detector_id: str
    interaction: str
    material: str
    geometry: str
    readout: str
    thermal_regime: str
    noise_model: str
    calibration_model: str
    failure_modes: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObservationCandidate:
    candidate_id: str
    observable_ids: tuple[str, ...]
    sensor_ids: tuple[str, ...]
    expected_information_gain: float
    discrimination_power: float
    calibration_confidence: float
    evidence_independence: float
    resource_cost: float = 0.0
    risk: float = 0.0
    complexity: float = 0.0
    epistemic_debt: float = 0.0

    def value(self) -> float:
        numerator = (
            max(self.expected_information_gain, 0.0)
            * max(self.discrimination_power, 0.0)
            * max(self.calibration_confidence, 0.0)
            * max(self.evidence_independence, 0.0)
        )
        denominator = 1.0 + sum(
            max(x, 0.0)
            for x in (self.resource_cost, self.risk, self.complexity, self.epistemic_debt)
        )
        return numerator / denominator


@dataclass(frozen=True)
class ObservatoryGenome:
    genome_id: str
    question_id: str
    hypothesis_ids: tuple[str, ...]
    observable_ids: tuple[str, ...]
    sensor_ids: tuple[str, ...]
    platform_ids: tuple[str, ...] = ()
    network_mode: str = "virtual"
    invariants: tuple[str, ...] = (
        "Generator != Judge",
        "Generated != Verified",
        "Simulation != Observation",
        "ClaimScope <= EvidenceScope",
        "NO_ACTION is valid",
    )
    permissions: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def digest(self) -> str:
        payload = {
            "genome_id": self.genome_id,
            "question_id": self.question_id,
            "hypothesis_ids": self.hypothesis_ids,
            "observable_ids": self.observable_ids,
            "sensor_ids": self.sensor_ids,
            "platform_ids": self.platform_ids,
            "network_mode": self.network_mode,
            "invariants": self.invariants,
            "permissions": self.permissions,
            "provenance": self.provenance,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObservationReceipt:
    receipt_id: str
    event_id: str
    sensor_ids: tuple[str, ...]
    calibration_versions: Mapping[str, str]
    raw_data_hashes: tuple[str, ...]
    processing_pipeline: str
    uncertainty: float
    generator_id: str
    verifier_id: str
    provenance: tuple[str, ...]
    excluded_data: tuple[str, ...] = ()
    alternative_explanations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SensoriumMemory:
    positive: tuple[str, ...] = field(default_factory=tuple)
    negative: tuple[str, ...] = field(default_factory=tuple)
    unresolved: tuple[str, ...] = field(default_factory=tuple)
