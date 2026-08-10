from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class BalanceNode:
    node_id: str
    net_supply: float = 0.0

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id required")
        if not math.isfinite(self.net_supply):
            raise ValueError("net_supply must be finite")


@dataclass(frozen=True, slots=True)
class DirectedArc:
    source_id: str
    target_id: str
    capacity: float
    unit_cost: float
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("arc endpoints required")
        if self.capacity < 0 or not math.isfinite(self.capacity):
            raise ValueError("capacity must be finite and non-negative")
        if self.unit_cost < 0 or not math.isfinite(self.unit_cost):
            raise ValueError("unit_cost must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class DirectedAllocation:
    source_id: str
    target_id: str
    quantity: float
    unit_cost: float
    label: str | None = None


@dataclass(frozen=True, slots=True)
class GeneralFlowResult:
    total_flow: float
    total_cost: float
    allocations: tuple[DirectedAllocation, ...]
    unmet_demand: float
    unused_supply: float
    optimality_certified: bool = True
    claim_boundary: str = "finite_single_commodity_min_cost_max_flow_only"


class _Edge:
    __slots__ = ("to", "rev", "capacity", "cost", "initial")

    def __init__(self, to: int, rev: int, capacity: float, cost: float) -> None:
        self.to = to
        self.rev = rev
        self.capacity = capacity
        self.cost = cost
        self.initial = capacity


def _add(graph: list[list[_Edge]], u: int, v: int, capacity: float, cost: float) -> _Edge:
    forward = _Edge(v, len(graph[v]), capacity, cost)
    reverse = _Edge(u, len(graph[u]), 0.0, -cost)
    graph[u].append(forward)
    graph[v].append(reverse)
    return forward


def min_cost_general_flow(nodes: tuple[BalanceNode, ...], arcs: tuple[DirectedArc, ...]) -> GeneralFlowResult:
    """Exact deterministic min-cost maximum flow on a finite directed single-commodity graph."""
    ids = [node.node_id for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate node_id")
    index = {node.node_id: i + 1 for i, node in enumerate(nodes)}
    for arc in arcs:
        if arc.source_id not in index or arc.target_id not in index:
            raise KeyError("arc endpoint is not a declared node")

    source = 0
    sink = len(nodes) + 1
    count = sink + 1
    graph: list[list[_Edge]] = [[] for _ in range(count)]
    total_supply = 0.0
    total_demand = 0.0
    for node in nodes:
        if node.net_supply > 0:
            _add(graph, source, index[node.node_id], node.net_supply, 0.0)
            total_supply += node.net_supply
        elif node.net_supply < 0:
            _add(graph, index[node.node_id], sink, -node.net_supply, 0.0)
            total_demand += -node.net_supply

    arc_edges: list[tuple[DirectedArc, _Edge]] = []
    for arc in arcs:
        arc_edges.append((arc, _add(graph, index[arc.source_id], index[arc.target_id], arc.capacity, arc.unit_cost)))

    flow = 0.0
    cost = 0.0
    eps = 1e-12
    while True:
        distance = [math.inf] * count
        previous_node = [-1] * count
        previous_edge = [-1] * count
        distance[source] = 0.0
        for _ in range(count - 1):
            changed = False
            for u in range(count):
                if not math.isfinite(distance[u]):
                    continue
                for edge_index, edge in enumerate(graph[u]):
                    if edge.capacity <= eps:
                        continue
                    candidate = distance[u] + edge.cost
                    proposal = (u, edge_index)
                    existing = (previous_node[edge.to], previous_edge[edge.to])
                    if candidate < distance[edge.to] - eps or (
                        abs(candidate - distance[edge.to]) <= eps
                        and (existing == (-1, -1) or proposal < existing)
                    ):
                        distance[edge.to] = candidate
                        previous_node[edge.to] = u
                        previous_edge[edge.to] = edge_index
                        changed = True
            if not changed:
                break
        if previous_node[sink] == -1:
            break

        augment = math.inf
        v = sink
        while v != source:
            u = previous_node[v]
            edge = graph[u][previous_edge[v]]
            augment = min(augment, edge.capacity)
            v = u
        if not math.isfinite(augment) or augment <= eps:
            break

        v = sink
        path_cost = 0.0
        while v != source:
            u = previous_node[v]
            edge = graph[u][previous_edge[v]]
            path_cost += edge.cost
            edge.capacity -= augment
            graph[v][edge.rev].capacity += augment
            v = u
        flow += augment
        cost += augment * path_cost

    allocations: list[DirectedAllocation] = []
    for arc, edge in arc_edges:
        used = edge.initial - edge.capacity
        if used > eps:
            allocations.append(DirectedAllocation(arc.source_id, arc.target_id, used, arc.unit_cost, arc.label))
    allocations.sort(key=lambda item: (item.source_id, item.target_id, item.unit_cost, item.label or ""))
    return GeneralFlowResult(
        total_flow=flow,
        total_cost=cost,
        allocations=tuple(allocations),
        unmet_demand=max(0.0, total_demand - flow),
        unused_supply=max(0.0, total_supply - flow),
    )
