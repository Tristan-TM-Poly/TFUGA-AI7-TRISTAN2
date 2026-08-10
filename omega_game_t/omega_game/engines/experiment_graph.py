from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from .campaign import CampaignCheckpoint, CampaignManifest
from .campaign_coordinator import CoordinatorLedger


SELECTION_ACTIONS = {"retain", "promote", "quarantine", "archive"}


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ExperimentNode:
    node_id: str
    kind: str
    attributes: dict[str, Any]
    evidence_receipts: tuple[str, ...]
    node_receipt: str

    @classmethod
    def create(
        cls,
        node_id: str,
        kind: str,
        *,
        attributes: Mapping[str, Any] | None = None,
        evidence_receipts: Iterable[str] = (),
    ) -> "ExperimentNode":
        if not node_id or not kind:
            raise ValueError("node_id and kind cannot be empty")
        receipts = tuple(sorted(set(str(value) for value in evidence_receipts if str(value))))
        body = {
            "node_id": node_id,
            "kind": kind,
            "attributes": dict(attributes or {}),
            "evidence_receipts": list(receipts),
        }
        return cls(
            node_id=node_id,
            kind=kind,
            attributes=body["attributes"],
            evidence_receipts=receipts,
            node_receipt=_canonical_hash(body),
        )

    def body(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "attributes": self.attributes,
            "evidence_receipts": list(self.evidence_receipts),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "node_receipt": self.node_receipt}


@dataclass(frozen=True)
class ExperimentEdge:
    source: str
    target: str
    kind: str
    attributes: dict[str, Any]
    edge_receipt: str

    @classmethod
    def create(
        cls,
        source: str,
        target: str,
        kind: str,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> "ExperimentEdge":
        if not source or not target or not kind:
            raise ValueError("edge source/target/kind cannot be empty")
        body = {
            "source": source,
            "target": target,
            "kind": kind,
            "attributes": dict(attributes or {}),
        }
        return cls(**body, edge_receipt=_canonical_hash(body))

    def body(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "attributes": self.attributes,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "edge_receipt": self.edge_receipt}


@dataclass(frozen=True)
class SelectionDecision:
    decision_id: str
    subject_node_id: str
    action: str
    evidence_receipts: tuple[str, ...]
    score_components: dict[str, float] = field(default_factory=dict)
    rationale_code: str = "unspecified"

    def validate(self) -> None:
        if not self.decision_id or not self.subject_node_id:
            raise ValueError("decision identifiers cannot be empty")
        if self.action not in SELECTION_ACTIONS:
            raise ValueError(f"unsupported selection action: {self.action}")
        if not self.evidence_receipts:
            raise ValueError("selection decision must cite at least one evidence receipt")
        for key, value in self.score_components.items():
            if not key:
                raise ValueError("score component name cannot be empty")
            float(value)

    @property
    def decision_receipt(self) -> str:
        self.validate()
        return _canonical_hash(self.to_dict(include_receipt=False))

    def to_dict(self, *, include_receipt: bool = True) -> dict[str, Any]:
        payload = {
            "decision_id": self.decision_id,
            "subject_node_id": self.subject_node_id,
            "action": self.action,
            "evidence_receipts": sorted(set(self.evidence_receipts)),
            "score_components": {key: float(self.score_components[key]) for key in sorted(self.score_components)},
            "rationale_code": self.rationale_code,
        }
        if include_receipt:
            payload["decision_receipt"] = _canonical_hash(payload)
        return payload


@dataclass(frozen=True)
class ExperimentGraphAudit:
    accepted: bool
    flags: tuple[str, ...]
    graph_receipt: str
    missing_decision_evidence: dict[str, tuple[str, ...]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "flags": list(self.flags),
            "graph_receipt": self.graph_receipt,
            "missing_decision_evidence": {
                key: list(value) for key, value in sorted(self.missing_decision_evidence.items())
            },
        }


@dataclass
class ExperimentGraph:
    graph_id: str
    nodes: dict[str, ExperimentNode] = field(default_factory=dict)
    edges: list[ExperimentEdge] = field(default_factory=list)

    def add_node(self, node: ExperimentNode) -> ExperimentNode:
        existing = self.nodes.get(node.node_id)
        if existing is not None:
            if existing.node_receipt != node.node_receipt:
                raise ValueError(f"conflicting node definition: {node.node_id}")
            return existing
        self.nodes[node.node_id] = node
        return node

    def create_node(
        self,
        node_id: str,
        kind: str,
        *,
        attributes: Mapping[str, Any] | None = None,
        evidence_receipts: Iterable[str] = (),
    ) -> ExperimentNode:
        return self.add_node(
            ExperimentNode.create(
                node_id,
                kind,
                attributes=attributes,
                evidence_receipts=evidence_receipts,
            )
        )

    def add_edge(self, edge: ExperimentEdge) -> ExperimentEdge:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("experiment edge endpoints must exist before edge insertion")
        if any(existing.edge_receipt == edge.edge_receipt for existing in self.edges):
            return edge
        self.edges.append(edge)
        return edge

    def connect(
        self,
        source: str,
        target: str,
        kind: str,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> ExperimentEdge:
        return self.add_edge(ExperimentEdge.create(source, target, kind, attributes=attributes))

    @property
    def graph_receipt(self) -> str:
        return _canonical_hash(
            {
                "graph_id": self.graph_id,
                "nodes": [self.nodes[node_id].to_dict() for node_id in sorted(self.nodes)],
                "edges": [edge.to_dict() for edge in sorted(self.edges, key=lambda item: item.edge_receipt)],
            }
        )

    def receipt_index(self) -> dict[str, tuple[str, ...]]:
        index: dict[str, list[str]] = {}
        for node in self.nodes.values():
            for receipt in node.evidence_receipts:
                index.setdefault(receipt, []).append(node.node_id)
        return {receipt: tuple(sorted(node_ids)) for receipt, node_ids in index.items()}

    def validate(self) -> None:
        if not self.graph_id:
            raise ValueError("graph_id cannot be empty")
        for node_id, node in self.nodes.items():
            if node.node_id != node_id:
                raise ValueError("experiment node key/id mismatch")
            if ExperimentNode.create(
                node.node_id,
                node.kind,
                attributes=node.attributes,
                evidence_receipts=node.evidence_receipts,
            ).node_receipt != node.node_receipt:
                raise ValueError(f"experiment node receipt mismatch: {node_id}")
        seen_edges: set[str] = set()
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError("dangling experiment edge")
            if ExperimentEdge.create(
                edge.source,
                edge.target,
                edge.kind,
                attributes=edge.attributes,
            ).edge_receipt != edge.edge_receipt:
                raise ValueError("experiment edge receipt mismatch")
            if edge.edge_receipt in seen_edges:
                raise ValueError("duplicate experiment edge")
            seen_edges.add(edge.edge_receipt)

    def audit(self) -> ExperimentGraphAudit:
        flags: list[str] = []
        try:
            self.validate()
        except ValueError as exc:
            flags.append(f"graph:{exc}")
        receipt_index = self.receipt_index()
        missing: dict[str, tuple[str, ...]] = {}
        for node in self.nodes.values():
            if node.kind != "selection_decision":
                continue
            required = tuple(node.attributes.get("evidence_receipts", ()))
            absent = tuple(sorted(receipt for receipt in required if receipt not in receipt_index))
            if absent:
                missing[node.node_id] = absent
                flags.append(f"missing_decision_evidence:{node.node_id}")
        return ExperimentGraphAudit(
            accepted=not flags,
            flags=tuple(sorted(set(flags))),
            graph_receipt=self.graph_receipt,
            missing_decision_evidence=missing,
        )

    def evidence_closure(self, node_id: str) -> tuple[str, ...]:
        if node_id not in self.nodes:
            raise ValueError(f"unknown experiment node: {node_id}")
        reverse: dict[str, list[str]] = {}
        for edge in self.edges:
            reverse.setdefault(edge.target, []).append(edge.source)
        visited: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for parent in sorted(reverse.get(current, [])):
                if parent not in visited:
                    visited.add(parent)
                    stack.append(parent)
        return tuple(sorted(visited))

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [self.nodes[node_id].to_dict() for node_id in sorted(self.nodes)],
            "edges": [edge.to_dict() for edge in sorted(self.edges, key=lambda item: item.edge_receipt)],
            "graph_receipt": self.graph_receipt,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def build_campaign_experiment_graph(
    manifest: CampaignManifest,
    *,
    checkpoint: CampaignCheckpoint | None = None,
    coordinator_ledger: CoordinatorLedger | None = None,
    memory_payload: Mapping[str, Any] | None = None,
    decisions: Iterable[SelectionDecision] = (),
) -> ExperimentGraph:
    manifest.validate()
    if checkpoint is not None:
        checkpoint.validate_for(manifest)
    if coordinator_ledger is not None:
        if coordinator_ledger.plan_receipt != manifest.plan_receipt:
            raise ValueError("coordinator ledger belongs to a different campaign plan")
        coordinator_ledger.validate_chain()

    graph = ExperimentGraph(graph_id=f"experiment:{manifest.plan_receipt}")
    reference_index: dict[str, str] = {}

    for agent in manifest.agents:
        attributes = asdict(agent)
        genome_receipt = _canonical_hash(attributes)
        node_id = f"agent:{agent.agent_id}"
        graph.create_node(node_id, "agent", attributes=attributes, evidence_receipts=(genome_receipt,))
        reference_index[agent.agent_id] = node_id
        reference_index[genome_receipt] = node_id

    for layout in manifest.layouts:
        node_id = f"layout:{layout.layout_hash}"
        graph.create_node(
            node_id,
            "layout",
            attributes=layout.normalized_dict(),
            evidence_receipts=(layout.layout_hash,),
        )
        reference_index[layout.layout_hash] = node_id

    for seed in manifest.seeds:
        node_id = f"seed:{seed}"
        graph.create_node(node_id, "seed", attributes={"seed": seed})
        reference_index[str(seed)] = node_id

    jobs_by_id = {job.job_id: job for job in manifest.jobs}
    for shard in manifest.shards:
        shard_id = f"shard:{shard.shard_id}"
        graph.create_node(
            shard_id,
            "shard",
            attributes={"shard_id": shard.shard_id, "job_count": len(shard.job_ids)},
        )
        for job_id in shard.job_ids:
            reference_index[f"shard-for:{job_id}"] = shard_id

    for job in manifest.jobs:
        node_id = f"job:{job.job_id}"
        graph.create_node(node_id, "job", attributes=job.to_dict(), evidence_receipts=(job.job_id,))
        reference_index[job.job_id] = node_id
        graph.connect(f"agent:{job.left_id}", node_id, "left_agent")
        graph.connect(f"agent:{job.right_id}", node_id, "right_agent")
        graph.connect(f"seed:{job.seed}", node_id, "uses_seed")
        if job.layout_hash is not None:
            graph.connect(f"layout:{job.layout_hash}", node_id, "uses_layout")
        graph.connect(reference_index[f"shard-for:{job.job_id}"], node_id, "contains_job")

    if checkpoint is not None:
        checkpoint_id = f"checkpoint:{checkpoint.checkpoint_receipt}"
        graph.create_node(
            checkpoint_id,
            "checkpoint",
            attributes={"completed_jobs": len(checkpoint.completed)},
            evidence_receipts=(checkpoint.checkpoint_receipt,),
        )
        reference_index[checkpoint.checkpoint_receipt] = checkpoint_id
        for job_id, result in sorted(checkpoint.completed.items()):
            result_id = f"result:{result.result_receipt}"
            graph.create_node(
                result_id,
                "result",
                attributes=result.to_dict(),
                evidence_receipts=(result.result_receipt, result.replay_hash),
            )
            reference_index[result.result_receipt] = result_id
            reference_index[result.replay_hash] = result_id
            graph.connect(f"job:{job_id}", result_id, "produces_result")
            graph.connect(result_id, checkpoint_id, "included_in_checkpoint")

    if coordinator_ledger is not None:
        previous_node_id: str | None = None
        for event in coordinator_ledger.events:
            event_id = f"event:{event.event_receipt}"
            graph.create_node(
                event_id,
                "coordinator_event",
                attributes=event.to_dict(),
                evidence_receipts=(event.event_receipt,),
            )
            reference_index[event.event_receipt] = event_id
            if previous_node_id is not None:
                graph.connect(previous_node_id, event_id, "causal_predecessor")
            previous_node_id = event_id
            if event.shard_id is not None and f"shard:{event.shard_id}" in graph.nodes:
                graph.connect(f"shard:{event.shard_id}", event_id, "orchestration_event")
            if event.worker_id:
                worker_id = f"worker:{event.worker_id}"
                if worker_id not in graph.nodes:
                    graph.create_node(worker_id, "worker", attributes={"worker_id": event.worker_id})
                graph.connect(worker_id, event_id, "worker_event")

    if memory_payload is not None:
        _add_memory_payload(graph, memory_payload, reference_index)

    for decision in decisions:
        _add_selection_decision(graph, decision)

    graph.validate()
    return graph


def _add_selection_decision(graph: ExperimentGraph, decision: SelectionDecision) -> None:
    decision.validate()
    if decision.subject_node_id not in graph.nodes:
        raise ValueError(f"selection subject not present in graph: {decision.subject_node_id}")
    node_id = f"decision:{decision.decision_id}"
    attributes = decision.to_dict(include_receipt=False)
    graph.create_node(
        node_id,
        "selection_decision",
        attributes=attributes,
        evidence_receipts=(decision.decision_receipt,),
    )
    graph.connect(decision.subject_node_id, node_id, "selection_subject")
    receipt_index = graph.receipt_index()
    for receipt in sorted(set(decision.evidence_receipts)):
        for evidence_node_id in receipt_index.get(receipt, ()):
            if evidence_node_id != node_id:
                graph.connect(evidence_node_id, node_id, "supports_decision", attributes={"receipt": receipt})


def _add_memory_payload(
    graph: ExperimentGraph,
    memory_payload: Mapping[str, Any],
    reference_index: Mapping[str, str],
) -> None:
    for polarity in ("plus", "minus"):
        section = memory_payload.get(polarity, {})
        if isinstance(section, Mapping):
            items = sorted(section.items(), key=lambda item: str(item[0]))
        elif isinstance(section, list):
            items = [(str(index), value) for index, value in enumerate(section)]
        else:
            continue
        for key, value in items:
            attributes = value if isinstance(value, dict) else {"value": value}
            record_receipt = _canonical_hash({"polarity": polarity, "key": str(key), "attributes": attributes})
            node_id = f"memory:{polarity}:{record_receipt}"
            graph.create_node(
                node_id,
                f"memory_{polarity}",
                attributes={"key": str(key), "record": attributes},
                evidence_receipts=(record_receipt,),
            )
            for reference in sorted(_string_values(attributes)):
                target = reference_index.get(reference)
                if target is not None:
                    graph.connect(target, node_id, "recorded_in_memory")


def _string_values(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, Mapping):
        for child in value.values():
            found.update(_string_values(child))
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            found.update(_string_values(child))
    return found
