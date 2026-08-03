"""Typed records for Ω-SYNERGY-N-T∞ R2.

The package distinguishes observed coalition values from inferred interactions.
No interaction estimate grants scientific, commercial, publication, or merge authority.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Iterable
import hashlib
import json


def canonical_components(values: Iterable[str]) -> tuple[str, ...]:
    result=tuple(sorted({str(v).strip() for v in values if str(v).strip()}))
    return result


def stable_id(prefix: str, *parts: object, length: int=16) -> str:
    payload=json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return f"{prefix}-{hashlib.sha256(payload.encode()).hexdigest()[:length]}"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k:_jsonable(v) for k,v in asdict(value).items()}
    if isinstance(value, Enum): return value.value
    if isinstance(value, dict): return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,set,frozenset)): return [_jsonable(v) for v in value]
    return value


class Serializable:
    def to_dict(self) -> dict[str,Any]: return _jsonable(self)


class Authority(str, Enum):
    REVIEW_ONLY="review_only"
    EXPERIMENTAL="experimental_evidence"
    REPLICATED="replicated_evidence"
    CANONICAL="canonical_validated"


class Certification(str, Enum):
    N0_CANDIDATE="N0_CANDIDATE"
    N1_TYPED="N1_TYPED_COMPATIBILITY"
    N2_CLOSURE="N2_THEORETICAL_CLOSURE"
    N3_PROTOTYPE="N3_MINIMAL_PROTOTYPE"
    N4_GROSS="N4_GROSS_GAIN_MEASURED"
    N5_PROPER="N5_PROPER_INTERACTION_MEASURED"
    N6_CAUSAL="N6_CAUSAL_INTERACTION"
    N7_ROBUST="N7_ROBUST"
    N8_REUSABLE="N8_REUSABLE"
    N9_EXTERNAL="N9_EXTERNALIZED"
    N10_CANONICAL="N10_CANONICAL"


@dataclass(frozen=True, slots=True)
class Context(Serializable):
    id: str="default"
    timestamp: str=""
    environment: str=""
    dataset: str=""
    repository_heads: dict[str,str]=field(default_factory=dict)
    validity_domain: list[str]=field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SubsetMeasurement(Serializable):
    components: tuple[str,...]
    value: float
    standard_error: float=0.0
    integration_cost: float=0.0
    debt: float=0.0
    residual_risk: float=0.0
    context_id: str="default"
    provenance: tuple[str,...]=()
    independent: bool=True

    def __post_init__(self) -> None:
        object.__setattr__(self,"components",canonical_components(self.components))
        for name in ("standard_error","integration_cost","debt","residual_risk"):
            if getattr(self,name)<0: raise ValueError(f"{name} must be non-negative")

    @property
    def key(self) -> frozenset[str]: return frozenset(self.components)


@dataclass(frozen=True, slots=True)
class InteractionEstimate(Serializable):
    components: tuple[str,...]
    order: int
    gross_value: float
    proper_interaction: float
    lower_order_value: float
    integration_cost: float
    debt: float
    residual_risk: float
    net_synergy: float
    standard_error: float
    interval_low: float
    interval_high: float
    purity: float
    necessity: dict[str,float]=field(default_factory=dict)
    context_id: str="default"
    authority: Authority=Authority.REVIEW_ONLY
    certification: Certification=Certification.N4_GROSS
    limitations: tuple[str,...]=()


@dataclass(frozen=True, slots=True)
class OrderBand(Serializable):
    order: int
    evaluated: int
    possible: int
    positive_count: int
    negative_count: int
    positive_energy: float
    negative_energy: float
    density: float
    efficiency: float
    mean_purity: float


@dataclass(frozen=True, slots=True)
class OrderSpectrum(Serializable):
    bands: tuple[OrderBand,...]
    normalized_energy: dict[int,float]
    order_entropy: float
    dominant_order: int|None


@dataclass(frozen=True, slots=True)
class Hyperedge(Serializable):
    id: str
    components: tuple[str,...]
    order: int
    proper_interaction: float|None=None
    net_synergy: float|None=None
    status: str="candidate"
    interfaces: tuple[str,...]=()
    evidence_refs: tuple[str,...]=()
    losses: tuple[str,...]=()
    risks: tuple[str,...]=()
    dependencies: tuple[str,...]=()
    context_id: str="default"


@dataclass(frozen=True, slots=True)
class ExperimentRun(Serializable):
    id: str
    active: tuple[str,...]
    inactive: tuple[str,...]
    replicate: int=1


@dataclass(frozen=True, slots=True)
class ExperimentDesign(Serializable):
    id: str
    components: tuple[str,...]
    design_type: str
    runs: tuple[ExperimentRun,...]
    identifiable_terms: tuple[tuple[str,...],...]
    alias_groups: tuple[tuple[str,...],...]
    assumptions: tuple[str,...]
    stopping_rules: tuple[str,...]
    authority: Authority=Authority.REVIEW_ONLY


@dataclass(frozen=True, slots=True)
class SearchCandidate(Serializable):
    components: tuple[str,...]
    order: int
    heuristic_score: float
    closure_gain: float
    compatibility: float
    expected_information_gain: float
    cost: float
    risk: float
    exploration: bool=False
    rationale: tuple[str,...]=()


@dataclass(frozen=True, slots=True)
class GateDecision(Serializable):
    candidate_id: str
    status: str
    passed: tuple[str,...]
    failed: tuple[str,...]
    warnings: tuple[str,...]
    maximum_authority: Authority=Authority.REVIEW_ONLY
    automatic_merge_allowed: bool=False
    automatic_publication_allowed: bool=False
    human_review_required: bool=True
