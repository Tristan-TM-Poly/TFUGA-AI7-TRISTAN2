"""Discrete causal reconstruction with explicit interventions and provenance."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps
from math import log
from typing import Any, Iterable, Mapping, Sequence

Value = str | int | float | bool
Record = Mapping[str, Value]


@dataclass(frozen=True, slots=True)
class CausalEdge:
    source: str
    target: str
    lag: int = 0
    confidence: float = 0.5
    mechanism: str = "hypothesized"
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("self causal edges are not supported")
        if self.lag < 0:
            raise ValueError("lag must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Intervention:
    variable: str
    value: Value
    context: Mapping[str, Value] = field(default_factory=dict)
    intervention_id: str = ""
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterventionResult:
    intervention: Intervention
    outcome_variable: str
    samples: tuple[Value, ...]

    @property
    def numeric_mean(self) -> float:
        numeric = [float(value) for value in self.samples if isinstance(value, (int, float, bool))]
        if len(numeric) != len(self.samples) or not numeric:
            raise TypeError("all samples must be numeric")
        return sum(numeric) / len(numeric)


@dataclass(slots=True)
class CausalGraph:
    variables: set[str] = field(default_factory=set)
    edges: list[CausalEdge] = field(default_factory=list)

    def add_edge(self, edge: CausalEdge) -> None:
        if any(item.source == edge.source and item.target == edge.target and item.lag == edge.lag for item in self.edges):
            raise ValueError("duplicate causal edge")
        self.variables.update((edge.source, edge.target))
        self.edges.append(edge)
        if self.has_cycle():
            self.edges.pop()
            raise ValueError("edge would introduce a directed cycle")

    def parents(self, variable: str) -> tuple[str, ...]:
        return tuple(sorted(edge.source for edge in self.edges if edge.target == variable))

    def children(self, variable: str) -> tuple[str, ...]:
        return tuple(sorted(edge.target for edge in self.edges if edge.source == variable))

    def has_cycle(self) -> bool:
        temporary: set[str] = set()
        permanent: set[str] = set()
        adjacency = {variable: self.children(variable) for variable in self.variables}

        def visit(node: str) -> bool:
            if node in permanent:
                return False
            if node in temporary:
                return True
            temporary.add(node)
            if any(visit(child) for child in adjacency.get(node, ())):
                return True
            temporary.remove(node)
            permanent.add(node)
            return False

        return any(visit(variable) for variable in tuple(self.variables))

    def topological_order(self) -> tuple[str, ...]:
        indegree = {variable: 0 for variable in self.variables}
        for edge in self.edges:
            indegree[edge.target] += 1
        ready = sorted(variable for variable, degree in indegree.items() if degree == 0)
        result: list[str] = []
        while ready:
            node = ready.pop(0)
            result.append(node)
            for child in self.children(node):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(result) != len(self.variables):
            raise ValueError("graph contains a cycle")
        return tuple(result)

    def descendants(self, variable: str) -> frozenset[str]:
        result: set[str] = set()
        frontier = list(self.children(variable))
        while frontier:
            node = frontier.pop()
            if node in result:
                continue
            result.add(node)
            frontier.extend(self.children(node))
        return frozenset(result)

    def digest(self) -> str:
        payload = {
            "variables": sorted(self.variables),
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "lag": e.lag,
                    "confidence": e.confidence,
                    "mechanism": e.mechanism,
                    "provenance": e.provenance,
                }
                for e in sorted(self.edges, key=lambda item: (item.source, item.target, item.lag))
            ],
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class EffectEstimate:
    treatment_variable: str
    outcome_variable: str
    treated_value: Value
    control_value: Value
    treated_mean: float
    control_mean: float
    average_treatment_effect: float
    treated_count: int
    control_count: int
    support_score: float
    warnings: tuple[str, ...] = ()


def intervention_effect(
    results: Sequence[InterventionResult],
    *,
    treatment_variable: str,
    outcome_variable: str,
    treated_value: Value,
    control_value: Value,
) -> EffectEstimate:
    treated: list[float] = []
    control: list[float] = []
    for result in results:
        if result.outcome_variable != outcome_variable:
            continue
        if result.intervention.variable != treatment_variable:
            continue
        target = treated if result.intervention.value == treated_value else control if result.intervention.value == control_value else None
        if target is not None:
            target.extend(float(item) for item in result.samples)
    if not treated or not control:
        raise ValueError("both treatment and control samples are required")
    treated_mean = sum(treated) / len(treated)
    control_mean = sum(control) / len(control)
    support = min(len(treated), len(control)) / max(len(treated), len(control))
    warnings = () if support >= 0.5 else ("Treatment and control sample counts are imbalanced.",)
    return EffectEstimate(
        treatment_variable=treatment_variable,
        outcome_variable=outcome_variable,
        treated_value=treated_value,
        control_value=control_value,
        treated_mean=treated_mean,
        control_mean=control_mean,
        average_treatment_effect=treated_mean - control_mean,
        treated_count=len(treated),
        control_count=len(control),
        support_score=support,
        warnings=warnings,
    )


def mutual_information(records: Iterable[Record], left: str, right: str) -> float:
    rows = list(records)
    if not rows:
        return 0.0
    joint: dict[tuple[Value, Value], int] = {}
    left_counts: dict[Value, int] = {}
    right_counts: dict[Value, int] = {}
    for row in rows:
        a, b = row[left], row[right]
        joint[(a, b)] = joint.get((a, b), 0) + 1
        left_counts[a] = left_counts.get(a, 0) + 1
        right_counts[b] = right_counts.get(b, 0) + 1
    total = len(rows)
    result = 0.0
    for (a, b), count in joint.items():
        p_ab = count / total
        p_a = left_counts[a] / total
        p_b = right_counts[b] / total
        result += p_ab * log(p_ab / (p_a * p_b), 2)
    return result


@dataclass(frozen=True, slots=True)
class EdgeCandidate:
    source: str
    target: str
    association_bits: float
    intervention_effect: float | None
    score: float
    status: str


def rank_edge_candidates(
    records: Sequence[Record],
    variables: Sequence[str],
    interventions: Sequence[InterventionResult] = (),
) -> tuple[EdgeCandidate, ...]:
    candidates: list[EdgeCandidate] = []
    for source in variables:
        for target in variables:
            if source == target:
                continue
            association = mutual_information(records, source, target)
            relevant = [item for item in interventions if item.intervention.variable == source and item.outcome_variable == target]
            effect: float | None = None
            if relevant:
                values = sorted({item.intervention.value for item in relevant}, key=repr)
                if len(values) >= 2:
                    estimate = intervention_effect(
                        relevant,
                        treatment_variable=source,
                        outcome_variable=target,
                        treated_value=values[-1],
                        control_value=values[0],
                    )
                    effect = estimate.average_treatment_effect
            score = association + (abs(effect) if effect is not None else 0.0)
            status = "interventionally_supported" if effect is not None else "association_only"
            candidates.append(EdgeCandidate(source, target, association, effect, score, status))
    return tuple(sorted(candidates, key=lambda item: (-item.score, item.source, item.target)))
