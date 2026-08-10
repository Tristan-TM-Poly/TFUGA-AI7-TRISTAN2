from __future__ import annotations

from dataclasses import dataclass

from .general_network import BalanceNode, DirectedArc, GeneralFlowResult, min_cost_general_flow


@dataclass(frozen=True, slots=True)
class TemporalBalance:
    node_id: str
    period: int
    net_supply: float


@dataclass(frozen=True, slots=True)
class TemporalArc:
    source_id: str
    target_id: str
    depart_period: int
    arrive_period: int
    capacity: float
    unit_cost: float
    label: str | None = None

    def __post_init__(self) -> None:
        if self.arrive_period < self.depart_period:
            raise ValueError("temporal arcs cannot travel backward in time")


def _temporal_id(node_id: str, period: int) -> str:
    return f"{node_id}@{period}"


def solve_time_expanded_flow(
    balances: tuple[TemporalBalance, ...],
    arcs: tuple[TemporalArc, ...],
    *,
    holdover_nodes: tuple[str, ...] = (),
    periods: tuple[int, ...] = (),
    holdover_capacity: float = 1e18,
    holdover_unit_cost: float = 0.0,
) -> GeneralFlowResult:
    node_keys = {(balance.node_id, balance.period) for balance in balances}
    for arc in arcs:
        node_keys.add((arc.source_id, arc.depart_period))
        node_keys.add((arc.target_id, arc.arrive_period))
    if periods:
        for node_id in holdover_nodes:
            for period in periods:
                node_keys.add((node_id, period))

    supply_by_key: dict[tuple[str, int], float] = {}
    for balance in balances:
        key = (balance.node_id, balance.period)
        supply_by_key[key] = supply_by_key.get(key, 0.0) + balance.net_supply

    nodes = tuple(
        BalanceNode(_temporal_id(node_id, period), supply_by_key.get((node_id, period), 0.0))
        for node_id, period in sorted(node_keys, key=lambda item: (item[1], item[0]))
    )
    directed = [
        DirectedArc(
            _temporal_id(arc.source_id, arc.depart_period),
            _temporal_id(arc.target_id, arc.arrive_period),
            arc.capacity,
            arc.unit_cost,
            arc.label,
        )
        for arc in arcs
    ]
    if periods:
        ordered_periods = sorted(set(periods))
        for node_id in holdover_nodes:
            for first, second in zip(ordered_periods, ordered_periods[1:]):
                directed.append(
                    DirectedArc(
                        _temporal_id(node_id, first),
                        _temporal_id(node_id, second),
                        holdover_capacity,
                        holdover_unit_cost,
                        "holdover",
                    )
                )
    return min_cost_general_flow(nodes, tuple(directed))
