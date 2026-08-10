from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

NODE_KINDS = (
    "claim", "assumption", "requirement", "test", "experiment", "observation",
    "evidence", "counterevidence", "residual", "decision", "action", "memory",
    "dataset", "validator", "environment",
)
EDGE_KINDS = (
    "depends_on", "assumes", "supported_by", "contradicted_by", "verified_by",
    "produced_by", "invalidates", "derived_from", "governs",
)
SEVERITIES = ("low", "medium", "high", "critical")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(value) for value in values)))


@dataclass(frozen=True)
class EpistemicNode:
    node_id: str
    kind: str
    label: str
    status: str = "UNKNOWN"
    criticality: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in NODE_KINDS:
            raise ValueError(f"unsupported node kind: {self.kind}")
        if not self.node_id or not self.label:
            raise ValueError("node_id and label are required")
        if not 1 <= self.criticality <= 5:
            raise ValueError("criticality must be in [1, 5]")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class EpistemicEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.relation not in EDGE_KINDS:
            raise ValueError(f"unsupported edge relation: {self.relation}")
        if self.source == self.target:
            raise ValueError("self edges are not allowed")
        if self.weight <= 0:
            raise ValueError("edge weight must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class EpistemicGraph:
    nodes: tuple[EpistemicNode, ...]
    edges: tuple[EpistemicEdge, ...]
    schema: str = "omega-ci-epistemic-graph/v3"

    @property
    def graph_id(self) -> str:
        return f"EGRAPH-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in sorted(self.nodes, key=lambda item: item.node_id)],
            "edges": [edge.to_dict() for edge in sorted(self.edges, key=lambda item: (item.source, item.target, item.relation))],
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "graph_id": self.graph_id, **self.identity_payload(), "remote_mutations": 0}


@dataclass(frozen=True)
class InvalidationResult:
    trigger_node_ids: tuple[str, ...]
    invalidated_node_ids: tuple[str, ...]
    propagation_paths: Mapping[str, tuple[str, ...]]
    reasons: Mapping[str, tuple[str, ...]]
    graph_id: str
    schema: str = "omega-ci-invalidation/v3"

    @property
    def result_id(self) -> str:
        return f"INVALIDATION-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "trigger_node_ids": list(self.trigger_node_ids),
            "invalidated_node_ids": list(self.invalidated_node_ids),
            "propagation_paths": {key: list(value) for key, value in sorted(self.propagation_paths.items())},
            "reasons": {key: list(value) for key, value in sorted(self.reasons.items())},
            "graph_id": self.graph_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "result_id": self.result_id, **self.identity_payload(), "automatic_actions": 0}


@dataclass(frozen=True)
class ProofDebtItem:
    debt_id: str
    category: str
    severity: str
    node_ids: tuple[str, ...]
    score: float
    reason: str
    remediation: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")
        if self.score < 0:
            raise ValueError("debt score cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["node_ids"] = list(self.node_ids)
        payload["remediation"] = list(self.remediation)
        return payload


@dataclass(frozen=True)
class ProofDebtReport:
    items: tuple[ProofDebtItem, ...]
    total_score: float
    counts_by_severity: Mapping[str, int]
    counts_by_category: Mapping[str, int]
    critical_open: int
    graph_id: str
    schema: str = "omega-ci-proof-debt/v3"

    @property
    def report_id(self) -> str:
        return f"DEBT-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "total_score": self.total_score,
            "counts_by_severity": dict(sorted(self.counts_by_severity.items())),
            "counts_by_category": dict(sorted(self.counts_by_category.items())),
            "critical_open": self.critical_open,
            "graph_id": self.graph_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload(), "automatic_merge_allowed": False}


@dataclass(frozen=True)
class TruthSLO:
    slo_id: str
    metric: str
    operator: str
    target: float
    severity: str
    description: str

    def __post_init__(self) -> None:
        if self.operator not in {">=", "<=", "==", ">", "<"}:
            raise ValueError(f"unsupported operator: {self.operator}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SLOEvaluation:
    slo_id: str
    metric: str
    observed: float
    operator: str
    target: float
    passed: bool
    severity: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TruthSLOReport:
    evaluations: tuple[SLOEvaluation, ...]
    metrics: Mapping[str, float]
    passed: bool
    critical_failures: int
    graph_id: str
    schema: str = "omega-ci-truth-slo/v3"

    @property
    def report_id(self) -> str:
        return f"TRUTHSLO-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evaluations": [item.to_dict() for item in self.evaluations],
            "metrics": dict(sorted(self.metrics.items())),
            "passed": self.passed,
            "critical_failures": self.critical_failures,
            "graph_id": self.graph_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload(), "human_review_required": True}


@dataclass(frozen=True)
class EvidenceConflict:
    claim_id: str
    supporting_node_ids: tuple[str, ...]
    contradicting_node_ids: tuple[str, ...]
    severity: str
    hypotheses: tuple[str, ...]
    discriminating_experiments: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("supporting_node_ids", "contradicting_node_ids", "hypotheses", "discriminating_experiments"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class ConflictReport:
    conflicts: tuple[EvidenceConflict, ...]
    open_conflicts: int
    critical_conflicts: int
    graph_id: str
    schema: str = "omega-ci-evidence-conflicts/v3"

    @property
    def report_id(self) -> str:
        return f"CONFLICTS-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "conflicts": [item.to_dict() for item in self.conflicts],
            "open_conflicts": self.open_conflicts,
            "critical_conflicts": self.critical_conflicts,
            "graph_id": self.graph_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload()}


@dataclass(frozen=True)
class ExperimentCandidate:
    experiment_id: str
    description: str
    expected_information_gain: float
    compute_cost: float
    human_cost: float
    safety_risk: float
    affected_claim_ids: tuple[str, ...]
    required_capability: str = "run_tests"

    @property
    def total_cost(self) -> float:
        return self.compute_cost + self.human_cost + self.safety_risk

    @property
    def utility(self) -> float:
        return self.expected_information_gain * max(0.0, 1.0 - self.safety_risk) / max(0.001, self.compute_cost + self.human_cost)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "affected_claim_ids": list(self.affected_claim_ids),
            "total_cost": round(self.total_cost, 6),
            "utility": round(self.utility, 6),
        }


@dataclass(frozen=True)
class ExperimentPortfolio:
    selected: tuple[ExperimentCandidate, ...]
    rejected: Mapping[str, str]
    budget: float
    consumed_budget: float
    expected_information_gain: float
    schema: str = "omega-ci-experiment-portfolio/v3"

    @property
    def portfolio_id(self) -> str:
        return f"EXPERIMENTS-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "selected": [item.to_dict() for item in self.selected],
            "rejected": dict(sorted(self.rejected.items())),
            "budget": self.budget,
            "consumed_budget": round(self.consumed_budget, 6),
            "expected_information_gain": round(self.expected_information_gain, 6),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "portfolio_id": self.portfolio_id,
            **self.identity_payload(),
            "execution_authorized": False,
            "remote_mutations": 0,
        }
