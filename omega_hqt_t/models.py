from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence
from .hashutil import sha256

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_type: str
    source_ref: str
    observed_at: str
    method: str
    uncertainty: float
    sensitivity: str = "public"
    oak_status: str = "synthetic_fixture"
    notes: str = ""
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    label: str
    level: str
    attributes: Mapping[str, Any] = field(default_factory=dict)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    sensitivity: str = "public"
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Hyperedge:
    edge_id: str
    relation: str
    sources: Sequence[str]
    targets: Sequence[str]
    attributes: Mapping[str, Any] = field(default_factory=dict)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    confidence: float = 1.0
    status: str = "synthetic_fixture"
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Corridor:
    corridor_id: str
    source: str
    target: str
    reactance_pu: float
    capacity_mw: float
    length_index: float
    climate_exposure: float
    repair_hours: float
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class RegionState:
    region_id: str
    demand_mw: float
    generation_mw: float
    reserve_mw: float
    storage_mwh: float = 0.0
    flexibility_fraction: float = 0.0
    critical_load_fraction: float = 0.2
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    demand_multiplier: float = 1.0
    hydro_multiplier: float = 1.0
    wind_multiplier: float = 1.0
    temperature_c: float = -10.0
    ice_severity: float = 0.0
    wind_severity: float = 0.0
    wildfire_severity: float = 0.0
    logistics_delay: float = 0.0
    workforce_availability: float = 1.0
    seed: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)
    @property
    def evidence_hash(self) -> str: return sha256(self.to_dict())

@dataclass(frozen=True)
class FlowResult:
    angles: Mapping[str, float]
    corridor_flows_mw: Mapping[str, float]
    overloads_mw: Mapping[str, float]
    disconnected_regions: Sequence[str]
    served_load_mw: float
    unserved_energy_mwh: float
    losses_proxy_mw: float
    balance_residual_mw: float
    finite: bool
    evidence_hash: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Intervention:
    intervention_id: str
    kind: str
    target_regions: Sequence[str]
    magnitude: float
    cost_index: float
    reversibility: float
    lead_time_index: float
    assumptions: Sequence[str] = field(default_factory=tuple)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class WorldOutcome:
    world_id: str
    intervention_id: str
    served_load_mw: float
    unserved_energy_mwh: float
    overload_mw: float
    restoration_hours: float
    cost_index: float
    resilience_score: float
    safety_passed: bool
    evidence_hash: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class Vote:
    chamber: str
    passed: bool
    score: float
    rationale: str
    blocking_reasons: Sequence[str] = field(default_factory=tuple)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class DecisionPackage:
    package_id: str
    mission: str
    recommended_interventions: Sequence[str]
    rejected_interventions: Sequence[str]
    votes: Sequence[Vote]
    claims: Mapping[str, bool]
    uncertainty: Mapping[str, float]
    counter_scenarios: Sequence[str]
    rollback_conditions: Sequence[str]
    status: str
    evidence_hash: str
    def to_dict(self) -> dict[str, Any]:
        data=asdict(self)
        data["votes"]=[v.to_dict() if hasattr(v, "to_dict") else v for v in self.votes]
        return data
