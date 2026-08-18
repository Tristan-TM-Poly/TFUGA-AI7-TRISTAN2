"""Trace-to-problem hypothesis compiler for Ω-INVARIANT-OPERATOR-GENESIS-T R0.2.

R0.2 moves one layer upstream from hand-supplied constraints. It mines candidate
invariants from finite graph-state traces using an explicit feature grammar,
rejects candidates that fail a held-out positive trace, packages the survivors
as a non-authorized ProblemHypothesis, and can feed that hypothesis into the
R0.1 exact operator oracle.

This is deliberately *not* raw-reality law discovery. The graph representation,
node domain, feature templates and positive-trace semantics are all inductive
biases and are carried in a ledger.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Iterable, Sequence

from .core import NamedInvariant, SynthesisReceipt, synthesize_minimal_operator
from .tsp import Edge, complete_graph_edges, edge


def _jsonable(value):
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, frozenset):
        return [_jsonable(item) for item in sorted(value, key=repr)]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


@dataclass(frozen=True, slots=True)
class GraphInvariantGrammarLedger:
    """Explicit R0.2 inductive biases for graph invariant hypothesis mining."""

    representation: str = "undirected_simple_edge_set"
    feature_templates: tuple[str, ...] = (
        "constant_edge_count",
        "endpoint_domain",
        "uniform_degree",
        "constant_component_count",
        "persistent_edge",
    )
    induction: str = "finite_positive_trace_conjunction"
    validation: str = "held_out_positive_trace"
    caveat: str = (
        "candidate invariant language is human-declared and remains an inductive bias; "
        "trace support is not a universal law"
    )


@dataclass(frozen=True, slots=True)
class InvariantHypothesis:
    kind: str
    parameter: object
    training_support: float
    holdout_support: float | None
    status: str
    description: str


@dataclass(frozen=True, slots=True)
class ObjectiveHypothesis:
    """Candidate objective metadata; discovery never implies authorization."""

    name: str
    provenance: str
    evidence: tuple[str, ...] = ()
    authorized: bool = False


@dataclass(frozen=True, slots=True)
class ProblemHypothesis:
    nodes: tuple[int, ...]
    reference_state: frozenset[Edge]
    hypotheses: tuple[InvariantHypothesis, ...]
    training_count: int
    holdout_count: int
    status: str
    grammar: GraphInvariantGrammarLedger
    objective: ObjectiveHypothesis | None = None
    objective_authorized: bool = False
    intervention_authorized: bool = False
    theorem_claimed: bool = False
    oak_boundaries: tuple[str, ...] = (
        "trace support != universal invariant",
        "feature grammar != discovered mathematics",
        "problem hypothesis != authorized objective",
        "constraint induction != causal intent discovery",
        "operator synthesis != intervention authority",
    )

    @property
    def accepted_hypotheses(self) -> tuple[InvariantHypothesis, ...]:
        return tuple(item for item in self.hypotheses if item.status == "TRACE_SUPPORTED")

    @property
    def rejected_hypotheses(self) -> tuple[InvariantHypothesis, ...]:
        return tuple(item for item in self.hypotheses if item.status.startswith("REJECTED_"))

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)


def _degree(state: frozenset[Edge], node: int) -> int:
    return sum(1 for a, b in state if a == node or b == node)


def _component_count(state: frozenset[Edge], nodes: tuple[int, ...]) -> int:
    adjacency = {node: set() for node in nodes}
    for a, b in state:
        if a not in adjacency or b not in adjacency:
            return len(nodes) + 1
        adjacency[a].add(b)
        adjacency[b].add(a)

    seen: set[int] = set()
    components = 0
    for node in nodes:
        if node in seen:
            continue
        components += 1
        seen.add(node)
        stack = [node]
        while stack:
            current = stack.pop()
            for nxt in adjacency[current] - seen:
                seen.add(nxt)
                stack.append(nxt)
    return components


def _holds(hypothesis: InvariantHypothesis, state: frozenset[Edge], nodes: tuple[int, ...]) -> bool:
    node_set = set(nodes)
    if hypothesis.kind == "edge_count_eq":
        return len(state) == int(hypothesis.parameter)
    if hypothesis.kind == "endpoints_in_domain":
        return all(a in node_set and b in node_set for a, b in state)
    if hypothesis.kind == "uniform_degree_eq":
        return all(_degree(state, node) == int(hypothesis.parameter) for node in nodes)
    if hypothesis.kind == "component_count_eq":
        return _component_count(state, nodes) == int(hypothesis.parameter)
    if hypothesis.kind == "contains_edge":
        raw = tuple(hypothesis.parameter)
        return edge(int(raw[0]), int(raw[1])) in state
    raise ValueError(f"unsupported hypothesis kind: {hypothesis.kind}")


def _support(
    hypothesis: InvariantHypothesis,
    states: tuple[frozenset[Edge], ...],
    nodes: tuple[int, ...],
) -> float | None:
    if not states:
        return None
    hits = sum(1 for state in states if _holds(hypothesis, state, nodes))
    return hits / len(states)


def _normalize_state(state: Iterable[Edge]) -> frozenset[Edge]:
    return frozenset(edge(int(a), int(b)) for a, b in state)


def mine_graph_problem(
    nodes: Sequence[int],
    training_states: Sequence[Iterable[Edge]],
    holdout_states: Sequence[Iterable[Edge]] = (),
    *,
    grammar: GraphInvariantGrammarLedger | None = None,
) -> ProblemHypothesis:
    """Mine trace-supported invariant candidates from a declared graph grammar.

    A candidate is promoted to TRACE_SUPPORTED only when it holds on every
    training state and every held-out positive state. Training-only support is
    never enough to authorize downstream synthesis.
    """

    ordered_nodes = tuple(dict.fromkeys(int(node) for node in nodes))
    if len(ordered_nodes) != len(nodes):
        raise ValueError("nodes must be unique")
    if len(ordered_nodes) < 3:
        raise ValueError("at least three nodes are required")

    training = tuple(_normalize_state(state) for state in training_states)
    holdout = tuple(_normalize_state(state) for state in holdout_states)
    if not training:
        raise ValueError("at least one training state is required")

    grammar = grammar or GraphInvariantGrammarLedger()
    specs: list[tuple[str, object, str]] = []

    if "constant_edge_count" in grammar.feature_templates:
        values = {len(state) for state in training}
        if len(values) == 1:
            value = next(iter(values))
            specs.append(("edge_count_eq", value, "edge count is constant on the training trace"))

    if "endpoint_domain" in grammar.feature_templates:
        specs.append(
            (
                "endpoints_in_domain",
                None,
                "all observed edge endpoints lie in the declared node domain",
            )
        )

    if "uniform_degree" in grammar.feature_templates:
        values = {_degree(state, node) for state in training for node in ordered_nodes}
        if len(values) == 1:
            value = next(iter(values))
            specs.append(
                (
                    "uniform_degree_eq",
                    value,
                    "all nodes share one observed degree across the training trace",
                )
            )

    if "constant_component_count" in grammar.feature_templates:
        values = {_component_count(state, ordered_nodes) for state in training}
        if len(values) == 1:
            value = next(iter(values))
            specs.append(
                (
                    "component_count_eq",
                    value,
                    "connected-component count is constant on the training trace",
                )
            )

    if "persistent_edge" in grammar.feature_templates:
        common = set(training[0])
        for state in training[1:]:
            common.intersection_update(state)
        for item in sorted(common):
            specs.append(
                (
                    "contains_edge",
                    item,
                    f"edge {item!r} persists across the training trace",
                )
            )

    hypotheses: list[InvariantHypothesis] = []
    for kind, parameter, description in specs:
        candidate = InvariantHypothesis(kind, parameter, 0.0, None, "CANDIDATE", description)
        training_support = _support(candidate, training, ordered_nodes)
        holdout_support = _support(candidate, holdout, ordered_nodes)
        assert training_support is not None

        if training_support != 1.0:
            status = "REJECTED_ON_TRAINING"
        elif not holdout:
            status = "TRAIN_SUPPORTED"
        elif holdout_support == 1.0:
            status = "TRACE_SUPPORTED"
        else:
            status = "REJECTED_ON_HOLDOUT"

        hypotheses.append(
            InvariantHypothesis(
                kind,
                parameter,
                training_support,
                holdout_support,
                status,
                description,
            )
        )

    status = (
        "TRACE_SUPPORTED"
        if holdout and any(item.status == "TRACE_SUPPORTED" for item in hypotheses)
        else "HOLD"
    )
    return ProblemHypothesis(
        nodes=ordered_nodes,
        reference_state=training[0],
        hypotheses=tuple(hypotheses),
        training_count=len(training),
        holdout_count=len(holdout),
        status=status,
        grammar=grammar,
    )


def materialize_invariants(problem: ProblemHypothesis) -> tuple[NamedInvariant[Edge], ...]:
    """Compile trace-supported hypotheses into R0.1 executable predicates."""

    if problem.status != "TRACE_SUPPORTED":
        raise ValueError("problem hypothesis is not supported on a held-out trace")

    nodes = problem.nodes
    materialized: list[NamedInvariant[Edge]] = []
    for index, hypothesis in enumerate(problem.accepted_hypotheses):
        name = f"mined_{index}_{hypothesis.kind}"
        materialized.append(
            NamedInvariant(
                name,
                lambda state, h=hypothesis: _holds(h, state, nodes),
                hypothesis.description,
            )
        )
    if not materialized:
        raise ValueError("no trace-supported invariant hypotheses")
    return tuple(materialized)


def synthesize_from_problem(
    problem: ProblemHypothesis,
    *,
    source: Iterable[Edge] | None = None,
    max_candidates: int = 100_000,
    max_witnesses: int = 64,
) -> SynthesisReceipt[Edge]:
    """Feed a held-out-supported problem hypothesis into the exact R0.1 oracle."""

    source_state = problem.reference_state if source is None else _normalize_state(source)
    return synthesize_minimal_operator(
        source_state,
        complete_graph_edges(problem.nodes),
        materialize_invariants(problem),
        max_candidates=max_candidates,
        max_witnesses=max_witnesses,
    )
