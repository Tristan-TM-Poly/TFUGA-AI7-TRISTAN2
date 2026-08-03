"""Canonical Transformation IR contracts for Ω-SYNERGY-OS-T∞ R0.2.

This module intentionally uses only the Python standard library. The IR is a
transport format between Tristan systems, not a truth engine. It keeps claims,
evidence, authority, uncertainty, risk, provenance and declared information
losses explicit so adapters cannot silently promote observations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "2.0"
MAX_AUTOMATED_AUTHORITY = "A3"


def utc_now() -> str:
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if raw:
        try:
            instant = datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except (ValueError, OverflowError, OSError) as exc:
            raise ValueError("SOURCE_DATE_EPOCH must be a valid integer timestamp") from exc
        return instant.replace(microsecond=0).isoformat()
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any, length: int = 20) -> str:
    material = "\x1f".join(canonical_json(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:length]}"


def _bounded(value: float, name: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return number


def _nonempty(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _unique_strings(values: Iterable[str]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


class ObjectKind(str, Enum):
    INTENT = "intent"
    CREATION = "creation"
    CAPABILITY = "capability"
    NEED = "need"
    INTERFACE = "interface"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    EXPERIMENT = "experiment"
    WORK_UNIT = "work_unit"
    GENERATOR = "generator"
    PR_GENE = "pr_gene"
    PROMOTION_PROOF = "promotion_proof"
    PORTFOLIO_DECISION = "portfolio_decision"
    PRODUCT_HYPOTHESIS = "product_hypothesis"
    RESIDUAL = "residual"
    POLICY = "policy"


class EpistemicStatus(str, Enum):
    OBSERVED = "observed"
    HYPOTHESIS = "hypothesis"
    FORMALIZED = "formalized"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    MEASURED = "measured"
    REPLICATED = "replicated"
    CANONICAL = "canonical"
    REFUTED = "refuted"
    SUPERSEDED = "superseded"


class AuthorityLevel(str, Enum):
    A0_OBSERVE = "A0"
    A1_DRAFT = "A1"
    A2_LOCAL_EXECUTION = "A2"
    A3_REVIEW_CANDIDATE = "A3"

    @property
    def ordinal(self) -> int:
        return int(self.value[1:])


class EvidenceState(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"
    REVOKED = "REVOKED"


class RelationKind(str, Enum):
    PRODUCES = "produces"
    CONSUMES = "consumes"
    SUPPORTS = "supports"
    FALSIFIES = "falsifies"
    BLOCKS = "blocks"
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    PROMOTES = "promotes"
    SUPERSEDES = "supersedes"
    RESOLVES = "resolves"
    EXPOSES = "exposes"
    ADAPTS_TO = "adapts_to"
    SELECTS = "selects"


class GateStatus(str, Enum):
    BLOCKED = "BLOCKED"
    ELIGIBLE_FOR_EXPERIMENT = "ELIGIBLE_FOR_EXPERIMENT"
    ELIGIBLE_FOR_HUMAN_REVIEW = "ELIGIBLE_FOR_HUMAN_REVIEW"


@dataclass(slots=True)
class IRNode(Serializable):
    id: str
    kind: ObjectKind
    name: str
    version: str = "0"
    status: EpistemicStatus = EpistemicStatus.OBSERVED
    authority: AuthorityLevel = AuthorityLevel.A0_OBSERVE
    input_types: list[str] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    uncertainty: float = 1.0
    risk: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.id = _nonempty(self.id, "node.id")
        self.name = _nonempty(self.name, "node.name")
        self.version = _nonempty(self.version, "node.version")
        for attr in ("input_types", "output_types", "capabilities", "needs", "claims", "evidence_refs", "provenance"):
            setattr(self, attr, _unique_strings(getattr(self, attr)))
        self.uncertainty = _bounded(self.uncertainty, "node.uncertainty")
        self.risk = _bounded(self.risk, "node.risk")
        if self.authority.ordinal > 3:
            raise ValueError("Transformation IR authority cannot exceed A3")

    @classmethod
    def build(cls, kind: ObjectKind, name: str, *, source_identity: Any, version: str = "0", **kwargs: Any) -> "IRNode":
        return cls(id=stable_id(kind.value.upper(), source_identity, name, version), kind=kind, name=name, version=version, **kwargs)


@dataclass(slots=True)
class IREdge(Serializable):
    id: str
    source: str
    target: str
    relation: RelationKind
    interface: str = ""
    preserved_invariants: list[str] = field(default_factory=list)
    declared_losses: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = _nonempty(self.id, "edge.id")
        self.source = _nonempty(self.source, "edge.source")
        self.target = _nonempty(self.target, "edge.target")
        self.preserved_invariants = _unique_strings(self.preserved_invariants)
        self.declared_losses = _unique_strings(self.declared_losses)
        self.evidence_refs = _unique_strings(self.evidence_refs)
        self.confidence = _bounded(self.confidence, "edge.confidence")

    @classmethod
    def build(cls, source: str, target: str, relation: RelationKind, **kwargs: Any) -> "IREdge":
        payload = {"source": source, "target": target, "relation": relation.value, "interface": kwargs.get("interface", ""), "preserved_invariants": sorted(kwargs.get("preserved_invariants", [])), "declared_losses": sorted(kwargs.get("declared_losses", []))}
        return cls(id=stable_id("EDGE", payload), source=source, target=target, relation=relation, **kwargs)


@dataclass(slots=True)
class ResidualRecord(Serializable):
    id: str
    code: str
    message: str
    severity: str
    subject_refs: list[str] = field(default_factory=list)
    reversible: bool = True
    next_action: str = "human_review"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = _nonempty(self.id, "residual.id")
        self.code = _nonempty(self.code, "residual.code")
        self.message = _nonempty(self.message, "residual.message")
        self.severity = self.severity.upper()
        if self.severity not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid residual severity")
        self.subject_refs = _unique_strings(self.subject_refs)

    @classmethod
    def build(cls, code: str, message: str, severity: str, subject_refs: Sequence[str] = (), **kwargs: Any) -> "ResidualRecord":
        return cls(id=stable_id("RES", code, message, sorted(subject_refs)), code=code, message=message, severity=severity, subject_refs=list(subject_refs), **kwargs)


@dataclass(slots=True)
class TransformationIR(Serializable):
    schema_version: str = SCHEMA_VERSION
    authority: AuthorityLevel = AuthorityLevel.A3_REVIEW_CANDIDATE
    generated_at: str = field(default_factory=utc_now)
    nodes: list[IRNode] = field(default_factory=list)
    edges: list[IREdge] = field(default_factory=list)
    source_heads: dict[str, str] = field(default_factory=dict)
    residuals: list[ResidualRecord] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.authority.ordinal > 3:
            raise ValueError("Transformation IR authority cannot exceed A3")
        self.policy_refs = _unique_strings(self.policy_refs)

    def add_node(self, node: IRNode) -> None:
        if any(existing.id == node.id for existing in self.nodes):
            raise ValueError(f"duplicate node id: {node.id}")
        self.nodes.append(node)

    def add_edge(self, edge: IREdge) -> None:
        if any(existing.id == edge.id for existing in self.edges):
            return
        known = {node.id for node in self.nodes}
        if edge.source not in known or edge.target not in known:
            raise ValueError(f"dangling edge: {edge.source} -> {edge.target}")
        self.edges.append(edge)

    def add_residual(self, residual: ResidualRecord) -> None:
        if not any(existing.id == residual.id for existing in self.residuals):
            self.residuals.append(residual)

    def validate(self) -> list[str]:
        errors: list[str] = []
        node_ids = [node.id for node in self.nodes]
        edge_ids = [edge.id for edge in self.edges]
        if len(node_ids) != len(set(node_ids)): errors.append("duplicate_node_ids")
        if len(edge_ids) != len(set(edge_ids)): errors.append("duplicate_edge_ids")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source not in known: errors.append(f"dangling_source:{edge.id}:{edge.source}")
            if edge.target not in known: errors.append(f"dangling_target:{edge.id}:{edge.target}")
        if self.authority.ordinal > 3: errors.append("authority_above_A3")
        return sorted(set(errors))

    def normalized_payload(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "authority": self.authority.value, "nodes": sorted((n.to_dict() for n in self.nodes), key=lambda x: x["id"]), "edges": sorted((e.to_dict() for e in self.edges), key=lambda x: x["id"]), "source_heads": dict(sorted(self.source_heads.items())), "residuals": sorted((r.to_dict() for r in self.residuals), key=lambda x: x["id"]), "policy_refs": sorted(self.policy_refs)}

    @property
    def content_digest(self) -> str:
        return digest(self.normalized_payload())


@dataclass(slots=True)
class SynergyConstellation(Serializable):
    id: str
    name: str
    systems: list[str]
    objective: str
    transformations: list[str]
    required_interfaces: list[str]
    metrics: list[str]
    baselines: list[str]
    falsifiers: list[str]
    rollback: list[str]
    risks: list[str]
    domains: list[str]
    closure_gain: float
    evidence_strength: float
    reuse: float
    product_value: float
    information_value: float
    reversibility: float
    integration_cost: float
    risk_score: float
    uncertainty: float
    stage: str = "S2_COMPLEMENTARITY"
    dependencies: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = _nonempty(self.id, "constellation.id")
        self.name = _nonempty(self.name, "constellation.name")
        self.objective = _nonempty(self.objective, "constellation.objective")
        for attr in ("systems", "transformations", "required_interfaces", "metrics", "baselines", "falsifiers", "rollback", "risks", "domains", "dependencies", "evidence_refs"):
            setattr(self, attr, _unique_strings(getattr(self, attr)))
        if len(self.systems) < 2: raise ValueError("a synergy constellation requires at least two systems")
        for attr in ("closure_gain", "evidence_strength", "reuse", "product_value", "information_value", "reversibility", "integration_cost", "risk_score", "uncertainty"):
            setattr(self, attr, _bounded(getattr(self, attr), f"constellation.{attr}"))

    @property
    def heuristic_utility(self) -> float:
        positive = 0.24*self.closure_gain + 0.18*self.evidence_strength + 0.18*self.reuse + 0.14*self.product_value + 0.14*self.information_value + 0.12*self.reversibility
        negative = 0.16*self.integration_cost + 0.14*self.risk_score + 0.10*self.uncertainty
        return round(max(-1.0, min(1.0, positive-negative)), 6)


@dataclass(slots=True)
class GateDecision(Serializable):
    constellation_id: str
    status: GateStatus
    satisfied_gates: list[str]
    missing_gates: list[str]
    evidence_refs: list[str]
    next_actions: list[str]
    human_review_required: bool = True
    automatic_merge_allowed: bool = False
    automatic_publication_allowed: bool = False
    authority: AuthorityLevel = AuthorityLevel.A3_REVIEW_CANDIDATE
    rationale: str = ""

    def __post_init__(self) -> None:
        self.constellation_id = _nonempty(self.constellation_id, "decision.constellation_id")
        for attr in ("satisfied_gates", "missing_gates", "evidence_refs", "next_actions"):
            setattr(self, attr, _unique_strings(getattr(self, attr)))
        if self.automatic_merge_allowed or self.automatic_publication_allowed or not self.human_review_required:
            raise ValueError("R0.2 requires human review and forbids automatic merge/publication")
        if self.authority.ordinal > 3: raise ValueError("decision authority cannot exceed A3")


@dataclass(slots=True)
class PortfolioSelection(Serializable):
    selected_ids: list[str]
    deferred_ids: list[str]
    blocked_ids: list[str]
    total_cost: float
    budget: float
    diversity_domains: list[str]
    rationale: list[str]
    authority: AuthorityLevel = AuthorityLevel.A3_REVIEW_CANDIDATE
    human_review_required: bool = True

    def __post_init__(self) -> None:
        for attr in ("selected_ids", "deferred_ids", "blocked_ids", "diversity_domains", "rationale"):
            setattr(self, attr, _unique_strings(getattr(self, attr)))
        if self.total_cost < 0 or self.budget < 0: raise ValueError("portfolio costs cannot be negative")
        if self.total_cost > self.budget + 1e-9: raise ValueError("portfolio exceeds budget")
        if not self.human_review_required: raise ValueError("portfolio selection requires human review")


@dataclass(slots=True)
class ArtifactReceipt(Serializable):
    path: str
    sha256: str
    size: int
    kind: str

    def __post_init__(self) -> None:
        self.path = _nonempty(self.path, "receipt.path")
        if len(self.sha256) != 64: raise ValueError("receipt.sha256 must be a SHA-256 digest")
        if self.size < 0: raise ValueError("receipt.size cannot be negative")


@dataclass(slots=True)
class BundleManifest(Serializable):
    schema_version: str
    bundle_id: str
    generated_at: str
    ir_digest: str
    merkle_root: str
    receipts: list[ArtifactReceipt]
    authority: AuthorityLevel = AuthorityLevel.A3_REVIEW_CANDIDATE
    human_review_required: bool = True
    automatic_merge_allowed: bool = False
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.automatic_merge_allowed or not self.human_review_required: raise ValueError("manifest requires human review and forbids merge")
        self.limitations = _unique_strings(self.limitations)


@dataclass(slots=True)
class SynergyOSBundle(Serializable):
    schema_version: str
    ir: TransformationIR
    constellations: list[SynergyConstellation]
    gate_decisions: list[GateDecision]
    portfolio: PortfolioSelection
    m_minus: list[ResidualRecord]
    authority: AuthorityLevel = AuthorityLevel.A3_REVIEW_CANDIDATE
    human_review_required: bool = True
    automatic_merge_allowed: bool = False
    automatic_publication_allowed: bool = False

    def __post_init__(self) -> None:
        if self.automatic_merge_allowed or self.automatic_publication_allowed or not self.human_review_required:
            raise ValueError("bundle requires human review and forbids irreversible actions")

    @property
    def content_digest(self) -> str:
        payload = self.to_dict()
        payload["ir"].pop("generated_at", None)
        return digest(payload)
