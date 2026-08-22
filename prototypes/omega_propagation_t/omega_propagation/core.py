from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Edge:
    """Typed transport edge for the toy propagation calculus.

    All values are normalized toy-model quantities unless a domain adapter
    explicitly gives them physical meaning.
    """

    source: str
    target: str
    latency: float = 1.0
    fidelity: float = 1.0
    risk: float = 0.0
    gain: float = 1.0
    capacity: float = float("inf")

    def __post_init__(self) -> None:
        if self.latency < 0:
            raise ValueError("latency must be >= 0")
        if not 0.0 <= self.fidelity <= 1.0:
            raise ValueError("fidelity must be in [0,1]")
        if self.risk < 0:
            raise ValueError("risk must be >= 0")
        if self.gain < 0:
            raise ValueError("gain must be >= 0")
        if self.capacity <= 0:
            raise ValueError("capacity must be > 0")


@dataclass(frozen=True)
class RouteReceipt:
    path: Tuple[str, ...]
    score: float
    latency: float
    fidelity: float
    cumulative_risk: float
    delivered: float


@dataclass(frozen=True)
class StopDecision:
    stop: bool
    reasons: Tuple[str, ...]


class PropagationGraph:
    """Small deterministic graph kernel for falsifiable propagation experiments."""

    def __init__(self, edges: Iterable[Edge] = ()) -> None:
        self._edges: List[Edge] = list(edges)
        self._adj: Dict[str, List[Edge]] = {}
        self._rebuild()

    @property
    def edges(self) -> Tuple[Edge, ...]:
        return tuple(self._edges)

    def _rebuild(self) -> None:
        self._adj = {}
        for edge in self._edges:
            self._adj.setdefault(edge.source, []).append(edge)
            self._adj.setdefault(edge.target, [])

    def add_edge(self, edge: Edge) -> None:
        self._edges.append(edge)
        self._adj.setdefault(edge.source, []).append(edge)
        self._adj.setdefault(edge.target, [])

    @staticmethod
    def _edge_cost(
        edge: Edge,
        risk_weight: float,
        fidelity_weight: float,
        latency_weight: float,
    ) -> float:
        return (
            latency_weight * edge.latency
            + risk_weight * edge.risk
            + fidelity_weight * (1.0 - edge.fidelity)
        )

    def best_route(
        self,
        source: str,
        target: str,
        *,
        amount: float = 1.0,
        risk_weight: float = 1.0,
        fidelity_weight: float = 1.0,
        latency_weight: float = 1.0,
    ) -> RouteReceipt:
        """Find the minimum surrogate-cost path, then compute path observables."""
        if amount < 0:
            raise ValueError("amount must be >= 0")
        if source == target:
            return RouteReceipt((source,), 0.0, 0.0, 1.0, 0.0, amount)

        queue: List[Tuple[float, str]] = [(0.0, source)]
        dist: Dict[str, float] = {source: 0.0}
        prev: Dict[str, Tuple[str, Edge]] = {}

        while queue:
            cost, node = heappop(queue)
            if cost != dist.get(node):
                continue
            if node == target:
                break
            for edge in self._adj.get(node, ()):
                step = self._edge_cost(
                    edge,
                    risk_weight=risk_weight,
                    fidelity_weight=fidelity_weight,
                    latency_weight=latency_weight,
                )
                new = cost + step
                if new < dist.get(edge.target, float("inf")):
                    dist[edge.target] = new
                    prev[edge.target] = (node, edge)
                    heappush(queue, (new, edge.target))

        if target not in dist:
            raise ValueError(f"no route from {source!r} to {target!r}")

        path_nodes = [target]
        path_edges: List[Edge] = []
        cursor = target
        while cursor != source:
            parent, edge = prev[cursor]
            path_edges.append(edge)
            path_nodes.append(parent)
            cursor = parent
        path_nodes.reverse()
        path_edges.reverse()

        latency = sum(e.latency for e in path_edges)
        fidelity = 1.0
        risk = 0.0
        delivered = amount
        for edge in path_edges:
            fidelity *= edge.fidelity
            risk += edge.risk
            delivered = min(delivered * edge.fidelity * edge.gain, edge.capacity)

        return RouteReceipt(
            path=tuple(path_nodes),
            score=dist[target],
            latency=latency,
            fidelity=fidelity,
            cumulative_risk=risk,
            delivered=delivered,
        )

    def reachable(
        self,
        source: str,
        *,
        removed_edges: Iterable[Tuple[str, str]] = (),
    ) -> Set[str]:
        removed = set(removed_edges)
        seen = {source}
        stack = [source]
        while stack:
            node = stack.pop()
            for edge in self._adj.get(node, ()):
                if (edge.source, edge.target) in removed:
                    continue
                if edge.target not in seen:
                    seen.add(edge.target)
                    stack.append(edge.target)
        return seen

    def minimum_edge_cut(
        self,
        source: str,
        targets: Iterable[str],
        *,
        max_edges: int = 18,
    ) -> Tuple[Tuple[str, str], ...]:
        """Exact brute-force edge cut for toy graphs.

        Deliberately refuses large search spaces rather than hiding exponential
        complexity. Production systems should replace this with a standard
        max-flow/min-cut implementation.
        """
        target_set = set(targets)
        unique_pairs = sorted({(e.source, e.target) for e in self._edges})
        if len(unique_pairs) > max_edges:
            raise ValueError(
                f"toy exact cut limited to {max_edges} edge-pairs; got {len(unique_pairs)}"
            )
        if not (self.reachable(source) & target_set):
            return ()

        for k in range(1, len(unique_pairs) + 1):
            for candidate in combinations(unique_pairs, k):
                if not (self.reachable(source, removed_edges=candidate) & target_set):
                    return tuple(candidate)
        return tuple(unique_pairs)

    def propagation_number(self, source: str) -> float:
        """Toy branching metric: average out-neighbors per reached node."""
        reached = self.reachable(source)
        if not reached:
            return 0.0
        counts = []
        for node in reached:
            counts.append(len({e.target for e in self._adj.get(node, ()) if e.target != node}))
        return sum(counts) / len(counts)


def epistemic_inflation(
    evidence_in: float,
    evidence_out: float,
    *,
    new_evidence: float = 0.0,
) -> float:
    """Positive excess evidence/confidence not justified by available evidence."""
    if min(evidence_in, evidence_out, new_evidence) < 0:
        raise ValueError("evidence values must be >= 0")
    return max(0.0, evidence_out - (evidence_in + new_evidence))


def meta_level_justified(
    *,
    verified_capability_gain: float,
    regenerability_gain: float = 0.0,
    transfer_gain: float = 0.0,
    future_option_gain: float = 0.0,
    complexity_cost: float = 0.0,
    risk_cost: float = 0.0,
    debt_cost: float = 0.0,
    compute_cost: float = 0.0,
    margin: float = 0.0,
) -> bool:
    benefit = (
        verified_capability_gain
        + regenerability_gain
        + transfer_gain
        + future_option_gain
    )
    cost = complexity_cost + risk_cost + debt_cost + compute_cost
    return benefit - cost > margin


def stop_rule(
    *,
    marginal_value: float,
    risk: float,
    risk_budget: float,
    evidence: float,
    evidence_minimum: float,
    saturation: float = 0.0,
    saturation_maximum: float = 1.0,
    residual: Optional[float] = None,
    residual_epsilon: Optional[float] = None,
) -> StopDecision:
    reasons: List[str] = []
    if marginal_value <= 0:
        reasons.append("non_positive_marginal_value")
    if risk > risk_budget:
        reasons.append("risk_budget_exceeded")
    if evidence < evidence_minimum:
        reasons.append("evidence_below_minimum")
    if saturation > saturation_maximum:
        reasons.append("saturation_exceeded")
    if residual is not None and residual_epsilon is not None and residual <= residual_epsilon:
        reasons.append("residual_closed")
    return StopDecision(stop=bool(reasons), reasons=tuple(reasons))
