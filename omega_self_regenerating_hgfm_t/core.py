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


@dataclass(frozen=True)
class CausalHyperedge(HyperedgeContract):
    intervention: str = ""
    outcome: str = ""
    confounders: tuple[str, ...] = ()
    counterfactual_ref: str = ""

    def causal_complete(self) -> bool:
        return bool(self.intervention and self.outcome and self.counterfactual_ref)


@dataclass(frozen=True)
class ExperimentHyperedge:
    experiment_id: str
    affected_claims: tuple[str, ...]
    observables: tuple[str, ...]
    baseline_refs: tuple[str, ...]
    expected_information_gain: float
    cost: float
    risk: float
    preregistered: bool = False

    def multiplex_ratio(self) -> float:
        return len(self.affected_claims) / max(self.cost, 1e-12)

    def utility(self) -> float:
        return (
            self.expected_information_gain * max(len(self.affected_claims), 1)
        ) / max(self.cost + self.risk, 1e-12)


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

    def record(self, cause: str, detector: str, countermeasure: str, transfer_rule: str,
               scope_pattern: tuple[str, ...] = ()) -> str:
        raw = "|".join((cause, detector, countermeasure, transfer_rule, ",".join(scope_pattern)))
        sig = sha256(raw.encode()).hexdigest()
        self.signatures[sig] = {
            "cause": cause, "detector": detector,
            "countermeasure": countermeasure, "transfer_rule": transfer_rule,
            "scope_pattern": list(scope_pattern),
        }
        return sig

    def prunes(self, edge: HyperedgeContract) -> bool:
        edge_tokens = set(edge.inputs) | set(edge.outputs) | {edge.operator}
        for rec in self.signatures.values():
            scope = set(rec.get("scope_pattern", ()))
            if scope and scope.issubset(edge_tokens):
                return True
        return False


@dataclass
class PlusMemory:
    patterns: dict[str, dict] = field(default_factory=dict)

    def record(self, pattern: str, evidence: str, transfer_hypothesis: str) -> str:
        raw = "|".join((pattern, evidence, transfer_hypothesis))
        sig = sha256(raw.encode()).hexdigest()
        self.patterns[sig] = {
            "pattern": pattern, "evidence": evidence,
            "transfer_hypothesis": transfer_hypothesis,
        }
        return sig


@dataclass(frozen=True)
class MorphogenesisPolicy:
    residual_weight: float = 1.0
    information_gain_weight: float = 1.0
    transfer_weight: float = 0.5
    cost_weight: float = 1.0
    risk_weight: float = 1.0
    debt_weight: float = 1.0

    def growth_score(self, residual: float, information_gain: float,
                     transferability: float, cost: float, risk: float, debt: float) -> float:
        num = (
            self.residual_weight * residual
            + self.information_gain_weight * information_gain
            + self.transfer_weight * transferability
        )
        den = (
            self.cost_weight * max(cost, 0)
            + self.risk_weight * max(risk, 0)
            + self.debt_weight * max(debt, 0)
            + 1e-12
        )
        return num / den


@dataclass
class FractalScaleMap:
    """Explicit zoom/coarse-grain correspondence between node IDs."""
    fine_to_coarse: dict[str, str] = field(default_factory=dict)

    def add(self, fine: str, coarse: str) -> None:
        self.fine_to_coarse[fine] = coarse

    def coarse_grain(self, fine_nodes: Iterable[str]) -> set[str]:
        return {self.fine_to_coarse.get(n, n) for n in fine_nodes}

    def zoom(self, coarse_node: str) -> set[str]:
        return {f for f, c in self.fine_to_coarse.items() if c == coarse_node}


@dataclass(frozen=True)
class CounterfactualWorld:
    world_id: str
    intervention: str
    assumptions: tuple[str, ...]
    predicted_outcomes: Mapping[str, float]


@dataclass
class RegenerationBench:
    original_verified_capabilities: set[str]

    def score(self, recovered: Iterable[str]) -> float:
        if not self.original_verified_capabilities:
            return 1.0
        return len(self.original_verified_capabilities & set(recovered)) / len(self.original_verified_capabilities)


class SelfRegeneratingHGFM:
    def __init__(self, policy: MorphogenesisPolicy | None = None):
        self.nodes: dict[str, EpistemicNode] = {}
        self.edges: dict[str, HyperedgeContract] = {}
        self.experiments: dict[str, ExperimentHyperedge] = {}
        self.worlds: dict[str, CounterfactualWorld] = {}
        self.residuals = ResidualField()
        self.m_minus = MinusMemory()
        self.m_plus = PlusMemory()
        self.scale_map = FractalScaleMap()
        self.policy = policy or MorphogenesisPolicy()

    def add_node(self, node: EpistemicNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: HyperedgeContract) -> None:
        missing = [n for n in (*edge.inputs, *edge.outputs) if n not in self.nodes]
        if missing:
            raise ValueError(f"unknown nodes in edge {edge.edge_id}: {missing}")
        if self.m_minus.prunes(edge):
            raise ValueError(f"edge {edge.edge_id} pruned by M-")
        self.edges[edge.edge_id] = edge

    def add_experiment(self, exp: ExperimentHyperedge) -> None:
        missing = [c for c in exp.affected_claims if c not in self.nodes]
        if missing:
            raise ValueError(f"unknown affected claims: {missing}")
        self.experiments[exp.experiment_id] = exp

    def add_world(self, world: CounterfactualWorld) -> None:
        self.worlds[world.world_id] = world

    def verified_edges(self) -> list[HyperedgeContract]:
        return [e for e in self.edges.values()
                if e.status == "verified" and e.proof_carrying()]

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

    def best_experiment(self) -> ExperimentHyperedge | None:
        if not self.experiments:
            return None
        return max(self.experiments.values(), key=lambda e: e.utility())

    def rank_growth(self, candidates: Sequence[Mapping]) -> list[dict]:
        out = []
        for c in candidates:
            score = self.policy.growth_score(
                float(c.get("residual",0)),
                float(c.get("information_gain",0)),
                float(c.get("transferability",0)),
                float(c.get("cost",1)),
                float(c.get("risk",0)),
                float(c.get("debt",0)),
            )
            out.append({"candidate": dict(c), "growth_score": score})
        return sorted(out, key=lambda x: x["growth_score"], reverse=True)

    def compare_worlds(self, observable: str) -> list[tuple[str, float]]:
        vals = []
        for w in self.worlds.values():
            if observable in w.predicted_outcomes:
                vals.append((w.world_id, float(w.predicted_outcomes[observable])))
        return sorted(vals, key=lambda x: x[1], reverse=True)

    def oak2_audit(self) -> dict:
        causal_edges = [e for e in self.edges.values() if isinstance(e, CausalHyperedge)]
        causal_complete = sum(e.causal_complete() for e in causal_edges)
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "experiments": len(self.experiments),
            "counterfactual_worlds": len(self.worlds),
            "verified_edges": len(self.verified_edges()),
            "proof_carrying_ratio": (
                sum(e.proof_carrying() for e in self.edges.values()) / len(self.edges)
                if self.edges else 1.0
            ),
            "causal_completeness_ratio": (
                causal_complete / len(causal_edges) if causal_edges else 1.0
            ),
            "best_experiment": (
                self.best_experiment().experiment_id if self.best_experiment() else None
            ),
            "residual_hotspots": self.residuals.top(5),
            "m_minus_count": len(self.m_minus.signatures),
        }

    def compress_to_kernel(self) -> dict:
        edges = self.verified_edges()
        keep_nodes = set()
        for e in edges:
            keep_nodes.update(e.inputs)
            keep_nodes.update(e.outputs)
        return {
            "nodes": [asdict(self.nodes[n]) for n in sorted(keep_nodes)],
            "edges": [asdict(e) | {"edge_type": type(e).__name__}
                      for e in sorted(edges, key=lambda e:e.edge_id)],
            "m_minus": self.m_minus.signatures,
            "m_plus": self.m_plus.patterns,
            "scale_map": self.scale_map.fine_to_coarse,
        }

    @classmethod
    def regenerate_from_kernel(cls, kernel: Mapping) -> "SelfRegeneratingHGFM":
        h = cls()
        for raw in kernel.get("nodes", []):
            h.add_node(EpistemicNode(**raw))
        for raw in kernel.get("edges", []):
            raw = dict(raw)
            edge_type = raw.pop("edge_type", "HyperedgeContract")
            for key in ("inputs","outputs","assumptions","evidence_refs","confounders"):
                if key in raw:
                    raw[key] = tuple(raw.get(key, ()))
            klass = CausalHyperedge if edge_type == "CausalHyperedge" else HyperedgeContract
            h.add_edge(klass(**raw))
        h.m_minus.signatures.update(kernel.get("m_minus", {}))
        h.m_plus.patterns.update(kernel.get("m_plus", {}))
        h.scale_map.fine_to_coarse.update(kernel.get("scale_map", {}))
        return h
