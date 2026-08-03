from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

from .hybrid import AffineFlow, HybridAutomaton, HybridTransition, Predicate, ResetRule


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float

    def validate(self) -> None:
        if not isfinite(self.lower) or not isfinite(self.upper) or self.lower > self.upper:
            raise ValueError("interval bounds must be finite and ordered")

    @classmethod
    def point(cls, value: float) -> "Interval":
        return cls(float(value), float(value))

    def add(self, other: "Interval") -> "Interval":
        self.validate()
        other.validate()
        return Interval(self.lower + other.lower, self.upper + other.upper)

    def scale(self, coefficient: float) -> "Interval":
        self.validate()
        if not isfinite(coefficient):
            raise ValueError("interval scale must be finite")
        first = coefficient * self.lower
        second = coefficient * self.upper
        return Interval(min(first, second), max(first, second))

    def widen(self, radius: float) -> "Interval":
        if radius < 0 or not isfinite(radius):
            raise ValueError("widening radius must be finite and non-negative")
        return Interval(self.lower - radius, self.upper + radius)

    @property
    def width(self) -> float:
        return self.upper - self.lower

    @property
    def midpoint(self) -> float:
        return 0.5 * (self.lower + self.upper)

    def to_dict(self) -> dict[str, float]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class ReachBox:
    bounds: Mapping[str, Interval]

    def validate(self, variables: Sequence[str]) -> None:
        if set(self.bounds) != set(variables):
            raise ValueError("reach box must cover automaton variables exactly")
        for interval in self.bounds.values():
            interval.validate()

    def to_dict(self) -> dict[str, Any]:
        return {name: interval.to_dict() for name, interval in self.bounds.items()}

    @property
    def volume_proxy(self) -> float:
        product = 1.0
        for interval in self.bounds.values():
            product *= max(interval.width, 1e-15)
        return product


@dataclass(frozen=True)
class ReachNode:
    node_id: str
    step: int
    time_s: float
    mode_id: str
    box: ReachBox
    parent_id: str | None
    transition_id: str | None
    invariant_definite: bool
    unsafe_possible: bool
    unsafe_definite: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "step": self.step,
            "time_s": self.time_s,
            "mode_id": self.mode_id,
            "box": self.box.to_dict(),
            "parent_id": self.parent_id,
            "transition_id": self.transition_id,
            "invariant_definite": self.invariant_definite,
            "unsafe_possible": self.unsafe_possible,
            "unsafe_definite": self.unsafe_definite,
        }


@dataclass(frozen=True)
class ReachabilityReport:
    automaton_hash: str
    integration_step_s: float
    steps_requested: int
    steps_completed: int
    nodes: tuple[ReachNode, ...]
    frontier_node_ids: tuple[str, ...]
    node_count: int
    transition_branch_count: int
    invariant_pruned_count: int
    uncertain_invariant_count: int
    unsafe_possible_count: int
    unsafe_definite_count: int
    truncated: bool
    execution_node_budget: int
    permanent_total_cap: None
    evidence_hash: str
    formal_reachability_proven: bool = False
    safety_certified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "automaton_hash": self.automaton_hash,
            "integration_step_s": self.integration_step_s,
            "steps_requested": self.steps_requested,
            "steps_completed": self.steps_completed,
            "nodes": [item.to_dict() for item in self.nodes],
            "frontier_node_ids": list(self.frontier_node_ids),
            "node_count": self.node_count,
            "transition_branch_count": self.transition_branch_count,
            "invariant_pruned_count": self.invariant_pruned_count,
            "uncertain_invariant_count": self.uncertain_invariant_count,
            "unsafe_possible_count": self.unsafe_possible_count,
            "unsafe_definite_count": self.unsafe_definite_count,
            "truncated": self.truncated,
            "execution_node_budget": self.execution_node_budget,
            "permanent_total_cap": self.permanent_total_cap,
            "evidence_hash": self.evidence_hash,
            "formal_reachability_proven": self.formal_reachability_proven,
            "safety_certified": self.safety_certified,
            "limitations": [
                "finite-horizon interval over-approximation",
                "explicit Euler enclosure without validated numerics",
                "guard crossings are sampled at declared time steps",
                "node budget bounds one execution and is not a permanent system cap",
                "absence of unsafe boxes is not a formal safety proof",
            ],
        }


def _predicate_interval_status(predicate: Predicate, box: ReachBox) -> tuple[bool, bool]:
    interval = box.bounds[predicate.variable]
    t = predicate.threshold
    eps = predicate.tolerance
    if predicate.comparator == "<=":
        return interval.lower <= t + eps, interval.upper <= t + eps
    if predicate.comparator == "<":
        return interval.lower < t - eps, interval.upper < t - eps
    if predicate.comparator == ">=":
        return interval.upper >= t - eps, interval.lower >= t - eps
    if predicate.comparator == ">":
        return interval.upper > t + eps, interval.lower > t + eps
    if predicate.comparator == "==":
        possible = interval.lower - eps <= t <= interval.upper + eps
        definite = interval.width <= 2 * eps and abs(interval.midpoint - t) <= eps
        return possible, definite
    possible_equal = interval.lower - eps <= t <= interval.upper + eps
    return True, not possible_equal


def _predicate_set_status(predicates: Sequence[Predicate], box: ReachBox) -> tuple[bool, bool]:
    if not predicates:
        return True, True
    statuses = [_predicate_interval_status(item, box) for item in predicates]
    return all(item[0] for item in statuses), all(item[1] for item in statuses)


def _affine_interval(flow: AffineFlow, box: ReachBox) -> Interval:
    result = Interval.point(flow.intercept)
    for variable, coefficient in flow.coefficients.items():
        result = result.add(box.bounds[variable].scale(float(coefficient)))
    return result


def _flow_step(automaton: HybridAutomaton, mode_id: str, box: ReachBox, dt_s: float) -> ReachBox:
    mode = automaton.mode_map()[mode_id]
    next_bounds = {
        variable: box.bounds[variable].add(_affine_interval(mode.flows[variable], box).scale(dt_s))
        for variable in automaton.variables
    }
    return ReachBox(next_bounds)


def _apply_reset_interval(reset: ResetRule, box: ReachBox) -> Interval:
    if reset.source_variable is None:
        source = Interval.point(0.0)
    else:
        source = box.bounds[reset.source_variable]
    return source.scale(reset.scale).add(Interval.point(reset.offset))


def _transition_box(transition: HybridTransition, box: ReachBox) -> ReachBox:
    updated = dict(box.bounds)
    before = ReachBox(dict(updated))
    for reset in transition.resets:
        updated[reset.target_variable] = _apply_reset_interval(reset, before)
    return ReachBox(updated)


def _unsafe_status(unsafe_conditions: Sequence[Predicate], box: ReachBox) -> tuple[bool, bool]:
    if not unsafe_conditions:
        return False, False
    return _predicate_set_status(unsafe_conditions, box)


def _node_id(step: int, mode_id: str, box: ReachBox, parent_id: str | None, transition_id: str | None) -> str:
    payload = {
        "step": step,
        "mode_id": mode_id,
        "box": box.to_dict(),
        "parent_id": parent_id,
        "transition_id": transition_id,
    }
    return _stable_hash(payload)[:24]


def _deduplicate(nodes: Sequence[ReachNode]) -> list[ReachNode]:
    unique: dict[str, ReachNode] = {}
    for node in nodes:
        signature = _stable_hash({
            "step": node.step,
            "mode_id": node.mode_id,
            "box": node.box.to_dict(),
        })
        unique.setdefault(signature, node)
    return sorted(unique.values(), key=lambda item: (item.mode_id, item.node_id))


def bounded_reachability(
    automaton: HybridAutomaton,
    *,
    initial_box: ReachBox,
    integration_step_s: float,
    steps: int,
    unsafe_conditions: Sequence[Predicate] = (),
    max_nodes_per_step: int = 4096,
    numerical_widening_per_step: float = 0.0,
) -> ReachabilityReport:
    automaton.validate()
    initial_box.validate(automaton.variables)
    if integration_step_s <= 0 or steps < 1 or max_nodes_per_step < 1:
        raise ValueError("reachability parameters are invalid")
    if numerical_widening_per_step < 0 or not isfinite(numerical_widening_per_step):
        raise ValueError("numerical widening must be finite and non-negative")
    for predicate in unsafe_conditions:
        predicate.validate(automaton.variables)

    initial_mode = automaton.mode_map()[automaton.initial_mode]
    invariant_possible, invariant_definite = _predicate_set_status(initial_mode.invariants, initial_box)
    if not invariant_possible:
        raise ValueError("initial box cannot satisfy the initial-mode invariant")
    unsafe_possible, unsafe_definite = _unsafe_status(unsafe_conditions, initial_box)
    initial = ReachNode(
        node_id=_node_id(0, automaton.initial_mode, initial_box, None, None),
        step=0,
        time_s=0.0,
        mode_id=automaton.initial_mode,
        box=initial_box,
        parent_id=None,
        transition_id=None,
        invariant_definite=invariant_definite,
        unsafe_possible=unsafe_possible,
        unsafe_definite=unsafe_definite,
    )
    all_nodes: list[ReachNode] = [initial]
    frontier = [initial]
    transition_branches = 0
    invariant_pruned = 0
    uncertain_invariants = int(not invariant_definite)
    truncated = False
    steps_completed = 0

    for step_index in range(1, steps + 1):
        candidates: list[ReachNode] = []
        for parent in frontier:
            flowed = _flow_step(automaton, parent.mode_id, parent.box, integration_step_s)
            if numerical_widening_per_step:
                flowed = ReachBox({
                    name: interval.widen(numerical_widening_per_step)
                    for name, interval in flowed.bounds.items()
                })
            mode = automaton.mode_map()[parent.mode_id]
            possible, definite = _predicate_set_status(mode.invariants, flowed)
            if possible:
                unsafe_p, unsafe_d = _unsafe_status(unsafe_conditions, flowed)
                candidates.append(ReachNode(
                    node_id=_node_id(step_index, parent.mode_id, flowed, parent.node_id, None),
                    step=step_index,
                    time_s=step_index * integration_step_s,
                    mode_id=parent.mode_id,
                    box=flowed,
                    parent_id=parent.node_id,
                    transition_id=None,
                    invariant_definite=definite,
                    unsafe_possible=unsafe_p,
                    unsafe_definite=unsafe_d,
                ))
                uncertain_invariants += int(not definite)
            else:
                invariant_pruned += 1

            for transition in automaton.outgoing(parent.mode_id):
                guard_possible, _ = _predicate_set_status(transition.guards, flowed)
                if not guard_possible:
                    continue
                transitioned = _transition_box(transition, flowed)
                target_mode = automaton.mode_map()[transition.target_mode]
                target_possible, target_definite = _predicate_set_status(target_mode.invariants, transitioned)
                if not target_possible:
                    invariant_pruned += 1
                    continue
                unsafe_p, unsafe_d = _unsafe_status(unsafe_conditions, transitioned)
                candidates.append(ReachNode(
                    node_id=_node_id(step_index, transition.target_mode, transitioned, parent.node_id, transition.transition_id),
                    step=step_index,
                    time_s=step_index * integration_step_s,
                    mode_id=transition.target_mode,
                    box=transitioned,
                    parent_id=parent.node_id,
                    transition_id=transition.transition_id,
                    invariant_definite=target_definite,
                    unsafe_possible=unsafe_p,
                    unsafe_definite=unsafe_d,
                ))
                transition_branches += 1
                uncertain_invariants += int(not target_definite)

        frontier = _deduplicate(candidates)
        if len(frontier) > max_nodes_per_step:
            frontier = sorted(
                frontier,
                key=lambda item: (
                    item.unsafe_definite is False,
                    item.unsafe_possible is False,
                    item.box.volume_proxy,
                    item.mode_id,
                    item.node_id,
                ),
            )[:max_nodes_per_step]
            truncated = True
        all_nodes.extend(frontier)
        steps_completed = step_index
        if not frontier:
            break

    unsafe_possible_count = sum(item.unsafe_possible for item in all_nodes)
    unsafe_definite_count = sum(item.unsafe_definite for item in all_nodes)
    payload = {
        "automaton_hash": automaton.evidence_hash,
        "integration_step_s": integration_step_s,
        "steps_requested": steps,
        "steps_completed": steps_completed,
        "nodes": [item.to_dict() for item in all_nodes],
        "frontier_node_ids": [item.node_id for item in frontier],
        "transition_branch_count": transition_branches,
        "invariant_pruned_count": invariant_pruned,
        "uncertain_invariant_count": uncertain_invariants,
        "unsafe_possible_count": unsafe_possible_count,
        "unsafe_definite_count": unsafe_definite_count,
        "truncated": truncated,
        "execution_node_budget": max_nodes_per_step,
        "permanent_total_cap": None,
    }
    return ReachabilityReport(
        automaton_hash=automaton.evidence_hash,
        integration_step_s=integration_step_s,
        steps_requested=steps,
        steps_completed=steps_completed,
        nodes=tuple(all_nodes),
        frontier_node_ids=tuple(item.node_id for item in frontier),
        node_count=len(all_nodes),
        transition_branch_count=transition_branches,
        invariant_pruned_count=invariant_pruned,
        uncertain_invariant_count=uncertain_invariants,
        unsafe_possible_count=unsafe_possible_count,
        unsafe_definite_count=unsafe_definite_count,
        truncated=truncated,
        execution_node_budget=max_nodes_per_step,
        permanent_total_cap=None,
        evidence_hash=_stable_hash(payload),
    )


def demo_initial_box() -> ReachBox:
    return ReachBox({
        "position_m": Interval(-0.001, 0.001),
        "velocity_mps": Interval(-0.002, 0.002),
        "temperature_k": Interval(293.0, 293.3),
        "clock_s": Interval(0.0, 0.0),
    })


def demo_unsafe_conditions() -> tuple[Predicate, ...]:
    return (Predicate("position_m", ">=", 0.27),)
