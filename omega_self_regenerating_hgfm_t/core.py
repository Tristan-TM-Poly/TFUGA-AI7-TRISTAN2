from __future__ import annotations
from dataclasses import dataclass, asdict, field
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

@dataclass(frozen=True)
class EpistemicNode:
    node_id: str
    kind: str
    payload: str
    status: str = "candidate"
    provenance: str = ""
    def digest(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

@dataclass(frozen=True)
class HyperedgeContract:
    edge_id: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    operator: str
    assumptions: tuple[str, ...] = ()
    verifier: str = ""
    falsifier: str = ""
    evidence_refs: tuple[str, ...] = ()
    uncertainty: float = 1.0
    status: str = "candidate"
    def proof_carrying(self) -> bool:
        return bool(self.verifier and self.falsifier and self.evidence_refs)

@dataclass
class ResidualField:
    values: dict[str, float] = field(default_factory=dict)
    def set(self, key: str, value: float) -> None:
        self.values[key] = float(value)
    def ranked(self) -> list[tuple[str, float]]:
        return sorted(self.values.items(), key=lambda kv: kv[1], reverse=True)
    def top(self, n: int = 1) -> list[tuple[str, float]]:
        return self.ranked()[:n]

@dataclass
class MinusMemory:
    signatures: dict[str, dict] = field(default_factory=dict)
    def record(self, cause: str, detector: str, countermeasure: str, transfer_rule: str) -> str:
        raw = "|".join((cause, detector, countermeasure, transfer_rule))
        sig = sha256(raw.encode()).hexdigest()
        self.signatures[sig] = {"cause": cause, "detector": detector, "countermeasure": countermeasure, "transfer_rule": transfer_rule}
        return sig

@dataclass
class PlusMemory:
    patterns: dict[str, dict] = field(default_factory=dict)
    def record(self, pattern: str, evidence: str, transfer_hypothesis: str) -> str:
        raw = "|".join((pattern, evidence, transfer_hypothesis))
        sig = sha256(raw.encode()).hexdigest()
        self.patterns[sig] = {"pattern": pattern, "evidence": evidence, "transfer_hypothesis": transfer_hypothesis}
        return sig

@dataclass(frozen=True)
class MorphogenesisPolicy:
    residual_weight: float = 1.0
    information_gain_weight: float = 1.0
    transfer_weight: float = 0.5
    cost_weight: float = 1.0
    risk_weight: float = 1.0
    debt_weight: float = 1.0
    def growth_score(self, *, residual: float, information_gain: float, transferability: float, cost: float, risk: float, debt: float) -> float:
        num = self.residual_weight * residual + self.information_gain_weight * information_gain + self.transfer_weight * transferability
        den = self.cost_weight * max(cost, 0.0) + self.risk_weight * max(risk, 0.0) + self.debt_weight * max(debt, 0.0) + 1e-12
        return num / den

@dataclass
class RegenerationBench:
    original_verified_capabilities: set[str]
    def score(self, recovered: Iterable[str]) -> float:
        original = self.original_verified_capabilities
        if not original:
            return 1.0
        return len(original.intersection(set(recovered))) / len(original)

class SelfRegeneratingHGFM:
    def __init__(self, policy: MorphogenesisPolicy | None = None):
        self.nodes: dict[str, EpistemicNode] = {}
        self.edges: dict[str, HyperedgeContract] = {}
        self.residuals = ResidualField()
        self.m_minus = MinusMemory()
        self.m_plus = PlusMemory()
        self.policy = policy or MorphogenesisPolicy()
    def add_node(self, node: EpistemicNode) -> None:
        self.nodes[node.node_id] = node
    def add_edge(self, edge: HyperedgeContract) -> None:
        missing = [n for n in (*edge.inputs, *edge.outputs) if n not in self.nodes]
        if missing:
            raise ValueError(f"unknown nodes in edge {edge.edge_id}: {missing}")
        self.edges[edge.edge_id] = edge
    def verified_edges(self) -> list[HyperedgeContract]:
        return [e for e in self.edges.values() if e.status == "verified" and e.proof_carrying()]
    def evidence_cone(self, target_node: str) -> set[str]:
        if target_node not in self.nodes:
            raise KeyError(target_node)
        cone = {target_node}
        changed = True
        while changed:
            changed = False
            for e in self.edges.values():
                if cone.intersection(e.outputs):
                    before = len(cone)
                    cone.update(e.inputs)
                    if len(cone) > before:
                        changed = True
        return cone
    def propose_growth(self, candidates: Sequence[Mapping]) -> list[dict]:
        scored = []
        for c in candidates:
            score = self.policy.growth_score(residual=float(c.get("residual", 0.0)), information_gain=float(c.get("information_gain", 0.0)), transferability=float(c.get("transferability", 0.0)), cost=float(c.get("cost", 1.0)), risk=float(c.get("risk", 0.0)), debt=float(c.get("debt", 0.0)))
            scored.append({"candidate": dict(c), "growth_score": score})
        return sorted(scored, key=lambda x: x["growth_score"], reverse=True)
    def oak2_audit(self) -> dict:
        verified = self.verified_edges()
        candidate = list(self.edges.values())
        proof_carrying_ratio = sum(e.proof_carrying() for e in candidate) / len(candidate) if candidate else 1.0
        return {"nodes": len(self.nodes), "edges": len(self.edges), "verified_edges": len(verified), "proof_carrying_ratio": proof_carrying_ratio, "residual_hotspots": self.residuals.top(5), "m_minus_count": len(self.m_minus.signatures), "m_plus_count": len(self.m_plus.patterns)}
    def compress_to_kernel(self) -> dict:
        edges = self.verified_edges()
        keep_nodes = set()
        for e in edges:
            keep_nodes.update(e.inputs); keep_nodes.update(e.outputs)
        return {"nodes": [asdict(self.nodes[n]) for n in sorted(keep_nodes)], "edges": [asdict(e) for e in sorted(edges, key=lambda e: e.edge_id)], "m_minus": self.m_minus.signatures, "m_plus": self.m_plus.patterns}
    @classmethod
    def regenerate_from_kernel(cls, kernel: Mapping) -> "SelfRegeneratingHGFM":
        h = cls()
        for raw in kernel.get("nodes", []): h.add_node(EpistemicNode(**raw))
        for raw in kernel.get("edges", []):
            raw = dict(raw)
            for key in ("inputs","outputs","assumptions","evidence_refs"): raw[key] = tuple(raw.get(key, ()))
            h.add_edge(HyperedgeContract(**raw))
        h.m_minus.signatures.update(kernel.get("m_minus", {})); h.m_plus.patterns.update(kernel.get("m_plus", {}))
        return h
