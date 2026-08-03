"""Typed domain models for Ω-SYNERGY-T∞.

The models deliberately separate observations, hypotheses, interfaces, evidence,
experiments and PR mutations. Names are not proof; every promoted object keeps
its authority, provenance and uncertainty.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from enum import Enum
import hashlib
import json
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_id(prefix: str, *parts: object, length: int = 16) -> str:
    material = "\x1f".join(json.dumps(p, sort_keys=True, ensure_ascii=False, default=str) for p in parts)
    return f"{prefix}-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:length]}"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in value]
    return value


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


class Authority(str, Enum):
    REVIEW_ONLY = "review_only_heuristic"
    EXPERIMENTAL = "experimental_evidence"
    REPLICATED = "replicated_evidence"
    CANONICAL = "canonical_validated"


class SynergyStage(str, Enum):
    S0_COEXISTENCE = "S0_COEXISTENCE"
    S1_RESONANCE = "S1_RESONANCE"
    S2_COMPLEMENTARITY = "S2_COMPLEMENTARITY"
    S3_INTERFACE = "S3_INTERFACE_DEFINED"
    S4_PROTOTYPE = "S4_PROTOTYPED"
    S5_GAIN = "S5_GAIN_MEASURED"
    S6_CAUSAL = "S6_CAUSAL_EVIDENCE"
    S7_ROBUST = "S7_ROBUST"
    S8_REUSABLE = "S8_REUSABLE"
    S9_META = "S9_META_SYNERGY"
    S10_GENERATIVE = "S10_GENERATIVE"
    S11_GOVERNED = "S11_GOVERNED_AUTOGENERATIVE"


@dataclass(slots=True)
class EvidenceRecord(Serializable):
    kind: str
    source: str
    strength: float = 0.0
    claim: str = ""
    hash: str = ""
    independent: bool = False
    observed_at: str = field(default_factory=utc_now)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.strength = max(0.0, min(1.0, float(self.strength)))
        if not self.hash:
            self.hash = stable_id("EVD", self.kind, self.source, self.claim)


@dataclass(slots=True)
class Capability(Serializable):
    id: str
    name: str
    input_types: list[str]
    output_types: list[str]
    domains: list[str]
    confidence: float = 0.0
    provenance: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    losses: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Need(Serializable):
    id: str
    name: str
    input_types: list[str]
    desired_output_types: list[str]
    domains: list[str]
    priority: float = 0.5
    provenance: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InterfaceContract(Serializable):
    id: str
    source_type: str
    target_type: str
    mappings: dict[str, str] = field(default_factory=dict)
    preserved_invariants: list[str] = field(default_factory=list)
    declared_losses: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=lambda: ["schema_validation", "provenance_integrity"])
    reversible: bool = True
    confidence: float = 0.0


@dataclass(slots=True)
class CreationDNA(Serializable):
    id: str
    name: str
    repository: str
    paths: list[str]
    mentions: int
    domains: list[str]
    tokens: list[str]
    capabilities: list[Capability] = field(default_factory=list)
    needs: list[Need] = field(default_factory=list)
    interfaces: list[InterfaceContract] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    risks: dict[str, float] = field(default_factory=dict)
    permissions: dict[str, str] = field(default_factory=dict)
    maturity: SynergyStage = SynergyStage.S1_RESONANCE
    expansion_options: list[str] = field(default_factory=list)
    uncertainty: dict[str, float] = field(default_factory=dict)

    @property
    def evidence_score(self) -> float:
        if not self.evidence:
            return 0.0
        weights = [record.strength * (1.15 if record.independent else 1.0) for record in self.evidence]
        return max(0.0, min(1.0, sum(weights) / len(weights)))

    @property
    def aggregate_risk(self) -> float:
        return max(self.risks.values(), default=0.0)


@dataclass(slots=True)
class SynergyTensor(Serializable):
    semantic_resonance: float
    complementarity: float
    interface_compatibility: float
    closure_gain: float
    evidence: float
    causal_readiness: float
    reuse: float
    option_value: float
    product_value: float
    risk: float
    integration_cost: float
    uncertainty: float
    debt: float
    total: float


@dataclass(slots=True)
class SynergyCandidate(Serializable):
    id: str
    systems: list[str]
    order: int
    stage: SynergyStage
    authority: Authority
    tensor: SynergyTensor
    transformations: list[str]
    matched_needs: list[str]
    proposed_interfaces: list[InterfaceContract]
    anti_synergy_flags: list[str]
    causal_hypothesis: str
    simplest_baseline: str
    provenance: list[str]
    generated_at: str = field(default_factory=utc_now)

    @property
    def score(self) -> float:
        return self.tensor.total

    @property
    def packet_id(self) -> str:
        """Backward-compatible research-packet identifier."""
        return self.id.replace("SYN-", "RPK-", 1)


@dataclass(slots=True)
class ExperimentPlan(Serializable):
    id: str
    candidate_id: str
    hypothesis: str
    baselines: list[str]
    ablations: list[str]
    controls: list[str]
    perturbations: list[str]
    metrics: list[str]
    success_criteria: list[str]
    failure_criteria: list[str]
    stopping_rules: list[str]
    oak_gates: list[str]
    rollback: list[str]
    expected_artifacts: list[str]
    authority: Authority = Authority.REVIEW_ONLY


@dataclass(slots=True)
class PRGene(Serializable):
    id: str
    title: str
    intention: str
    candidate_id: str
    paths: list[str]
    capabilities_added: list[str]
    needs_resolved: list[str]
    interfaces_provided: list[str]
    interfaces_consumed: list[str]
    tests: list[str]
    risks: dict[str, float]
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    rollback: list[str] = field(default_factory=list)
    option_value: float = 0.0
    authority: Authority = Authority.REVIEW_ONLY


@dataclass(slots=True)
class MetaSynergy(Serializable):
    id: str
    candidate_ids: list[str]
    ordered_systems: list[str]
    composition: list[str]
    conserved_invariants: list[str]
    propagated_losses: list[str]
    propagated_uncertainty: float
    estimated_value: float
    reversibility: float
    stage: SynergyStage = SynergyStage.S9_META
    authority: Authority = Authority.REVIEW_ONLY


@dataclass(slots=True)
class ProductHypothesis(Serializable):
    id: str
    candidate_id: str
    user: str
    problem: str
    offer: str
    proof_required: list[str]
    monetization: list[str]
    readiness: float
    blockers: list[str]
    authority: Authority = Authority.REVIEW_ONLY


def by_id(items: Iterable[Serializable]) -> dict[str, Serializable]:
    return {getattr(item, "id"): item for item in items}
