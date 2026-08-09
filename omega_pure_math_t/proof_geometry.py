"""Finite proof-hypergraph geometry and proof thermodynamics."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, log
from typing import Iterable


@dataclass(frozen=True)
class Inference:
    premises: tuple[str, ...]
    conclusion: str
    rule: str
    cost: float = 1.0

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("inference cost must be non-negative")


@dataclass
class ProofHypergraph:
    axioms: set[str] = field(default_factory=set)
    inferences: list[Inference] = field(default_factory=list)

    def add_inference(self, inference: Inference) -> None:
        self.inferences.append(inference)

    def closure(self) -> set[str]:
        known = set(self.axioms)
        changed = True
        while changed:
            changed = False
            for inference in self.inferences:
                if inference.conclusion in known:
                    continue
                if set(inference.premises) <= known:
                    known.add(inference.conclusion)
                    changed = True
        return known

    def proves(self, theorem: str) -> bool:
        return theorem in self.closure()

    def minimum_derivation_cost(self, theorem: str) -> float:
        """Bellman-style fixed point for finite monotone hypergraphs."""

        costs = {axiom: 0.0 for axiom in self.axioms}
        changed = True
        while changed:
            changed = False
            for inference in self.inferences:
                if not all(premise in costs for premise in inference.premises):
                    continue
                candidate = inference.cost + sum(costs[p] for p in inference.premises)
                previous = costs.get(inference.conclusion)
                if previous is None or candidate < previous:
                    costs[inference.conclusion] = candidate
                    changed = True
        return costs.get(theorem, float("inf"))


def proof_partition_function(costs: Iterable[float], beta: float) -> float:
    """Finite Z_T(β)=Σ exp(-β C(P))."""

    if beta < 0:
        raise ValueError("beta must be non-negative")
    values = tuple(float(cost) for cost in costs)
    if any(cost < 0 for cost in values):
        raise ValueError("proof costs must be non-negative")
    return sum(exp(-beta * cost) for cost in values)


def proof_free_energy(costs: Iterable[float], beta: float) -> float:
    """Finite formal free-energy analogue; beta must be >0."""

    if beta <= 0:
        raise ValueError("beta must be > 0")
    z = proof_partition_function(costs, beta)
    if z <= 0:
        raise ValueError("at least one finite proof cost is required")
    return -log(z) / beta


def expected_proof_cost(costs: Iterable[float], beta: float) -> float:
    values = tuple(float(cost) for cost in costs)
    z = proof_partition_function(values, beta)
    if z == 0:
        raise ValueError("partition function vanished")
    return sum(cost * exp(-beta * cost) for cost in values) / z
