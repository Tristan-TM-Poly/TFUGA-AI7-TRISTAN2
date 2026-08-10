from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class SupplyNode:
    node_id: str
    quantity: float

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id is required")
        if self.quantity < 0:
            raise ValueError("supply quantity must be non-negative")


@dataclass(frozen=True, slots=True)
class DemandNode:
    node_id: str
    quantity: float

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id is required")
        if self.quantity < 0:
            raise ValueError("demand quantity must be non-negative")


@dataclass(frozen=True, slots=True)
class TransferArc:
    source_id: str
    target_id: str
    capacity: float
    unit_cost: float
    label: str | None = None

    def __post_init__(self) -> None:
        if self.capacity < 0:
            raise ValueError("arc capacity must be non-negative")
        if not math.isfinite(self.unit_cost):
            raise ValueError("arc unit_cost must be finite")


@dataclass(frozen=True, slots=True)
class TransferAllocation:
    source_id: str
    target_id: str
    quantity: float
    unit_cost: float
    label: str | None = None


@dataclass(frozen=True, slots=True)
class TransportResult:
    total_flow: float
    total_cost: float
    allocations: tuple[TransferAllocation, ...]
    unmet_demand: float
    unused_supply: float
    optimality_certified: bool = True


class _Edge:
    __slots__ = ("to", "rev", "capacity", "cost", "initial_capacity")

    def __init__(self, to: int, rev: int, capacity: float, cost: float) -> None:
        self.to = to
        self.rev = rev
        self.capacity = capacity
        self.cost = cost
        self.initial_capacity = capacity


def _add_edge(graph: list[list[_Edge]], u: int, v: int, capacity: float, cost: float) -> _Edge:
    forward = _Edge(v, len(graph[v]), capacity, cost)
    reverse = _Edge(u, len(graph[u]), 0.0, -cost)
    graph[u].append(forward)
    graph[v].append(reverse)
    return forward


def min_cost_transport(
    supplies: tuple[SupplyNode, ...],
    demands: tuple[DemandNode, ...],
    arcs: tuple[TransferArc, ...],
) -> TransportResult:
    """Exact deterministic min-cost maximum flow for a bipartite transport network.

    Objective: maximize transported quantity first, then minimize total declared
    transfer cost among maximum-flow solutions. Bellman-Ford is used on the
    residual graph to remain dependency-free and auditable.
    """
    supply_ids = [node.node_id for node in supplies]
    demand_ids = [node.node_id for node in demands]
    if len(set(supply_ids)) != len(supply_ids):
        raise ValueError("duplicate supply node_id")
    if len(set(demand_ids)) != len(demand_ids):
        raise ValueError("duplicate demand node_id")

    s_index = {node.node_id: i for i, node in enumerate(supplies)}
    d_index = {node.node_id: i for i, node in enumerate(demands)}
    for arc in arcs:
        if arc.source_id not in s_index:
            raise KeyError(f"unknown supply node: {arc.source_id}")
        if arc.target_id not in d_index:
            raise KeyError(f"unknown demand node: {arc.target_id}")

    source = 0
    supply_offset = 1
    demand_offset = supply_offset + len(supplies)
    sink = demand_offset + len(demands)
    node_count = sink + 1
    graph: list[list[_Edge]] = [[] for _ in range(node_count)]

    for i, node in enumerate(supplies):
        _add_edge(graph, source, supply_offset + i, node.quantity, 0.0)
    for i, node in enumerate(demands):
        _add_edge(graph, demand_offset + i, sink, node.quantity, 0.0)

    arc_edges: list[tuple[TransferArc, _Edge]] = []
    for arc in arcs:
        edge = _add_edge(
            graph,
            supply_offset + s_index[arc.source_id],
            demand_offset + d_index[arc.target_id],
            arc.capacity,
            arc.unit_cost,
        )
        arc_edges.append((arc, edge))

    total_flow = 0.0
    total_cost = 0.0
    eps = 1e-12

    while True:
        dist = [math.inf] * node_count
        prev_node = [-1] * node_count
        prev_edge = [-1] * node_count
        dist[source] = 0.0

        for _ in range(node_count - 1):
            changed = False
            for u in range(node_count):
                if not math.isfinite(dist[u]):
                    continue
                for ei, edge in enumerate(graph[u]):
                    if edge.capacity <= eps:
                        continue
                    candidate = dist[u] + edge.cost
                    if candidate < dist[edge.to] - eps:
                        dist[edge.to] = candidate
                        prev_node[edge.to] = u
                        prev_edge[edge.to] = ei
                        changed = True
                    elif abs(candidate - dist[edge.to]) <= eps:
                        existing = (prev_node[edge.to], prev_edge[edge.to])
                        proposal = (u, ei)
                        if existing == (-1, -1) or proposal < existing:
                            prev_node[edge.to] = u
                            prev_edge[edge.to] = ei
                            changed = True
            if not changed:
                break

        if prev_node[sink] == -1:
            break

        augment = math.inf
        v = sink
        while v != source:
            u = prev_node[v]
            edge = graph[u][prev_edge[v]]
            augment = min(augment, edge.capacity)
            v = u
        if not math.isfinite(augment) or augment <= eps:
            break

        v = sink
        path_cost = 0.0
        while v != source:
            u = prev_node[v]
            edge = graph[u][prev_edge[v]]
            path_cost += edge.cost
            edge.capacity -= augment
            graph[v][edge.rev].capacity += augment
            v = u
        total_flow += augment
        total_cost += augment * path_cost

    allocations: list[TransferAllocation] = []
    for arc, edge in arc_edges:
        used = edge.initial_capacity - edge.capacity
        if used > eps:
            allocations.append(
                TransferAllocation(
                    source_id=arc.source_id,
                    target_id=arc.target_id,
                    quantity=used,
                    unit_cost=arc.unit_cost,
                    label=arc.label,
                )
            )
    allocations.sort(key=lambda item: (item.source_id, item.target_id, item.unit_cost, item.label or ""))

    total_supply = sum(node.quantity for node in supplies)
    total_demand = sum(node.quantity for node in demands)
    return TransportResult(
        total_flow=total_flow,
        total_cost=total_cost,
        allocations=tuple(allocations),
        unmet_demand=max(0.0, total_demand - total_flow),
        unused_supply=max(0.0, total_supply - total_flow),
        optimality_certified=True,
    )
