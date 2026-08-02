"""Synthetic protocol trace modeling and conservative state inference."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps
from typing import Iterable, Mapping, Sequence

Message = str
State = str


@dataclass(frozen=True, slots=True)
class ProtocolStep:
    request: Message
    response: Message
    latency_ms: float = 0.0
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class ProtocolTrace:
    steps: tuple[ProtocolStep, ...]
    reset_before: bool = True
    trace_id: str = ""
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProtocolTransition:
    source: State
    request: Message
    response: Message
    target: State
    observations: int = 1
    latency_min_ms: float = 0.0
    latency_max_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class ProtocolModel:
    states: tuple[State, ...]
    initial_state: State
    transitions: tuple[ProtocolTransition, ...]
    terminal_states: tuple[State, ...]
    conflicts: tuple[tuple[State, Message, tuple[Message, ...]], ...] = ()

    def transition_index(self) -> Mapping[tuple[State, Message], tuple[ProtocolTransition, ...]]:
        buckets: dict[tuple[State, Message], list[ProtocolTransition]] = defaultdict(list)
        for transition in self.transitions:
            buckets[(transition.source, transition.request)].append(transition)
        return {key: tuple(items) for key, items in buckets.items()}

    def replay(self, requests: Sequence[Message]) -> frozenset[tuple[tuple[Message, ...], State]]:
        index = self.transition_index()
        frontier: set[tuple[State, tuple[Message, ...]]] = {(self.initial_state, ())}
        for request in requests:
            next_frontier: set[tuple[State, tuple[Message, ...]]] = set()
            for state, responses in frontier:
                for transition in index.get((state, request), ()):
                    next_frontier.add((transition.target, responses + (transition.response,)))
            frontier = next_frontier
            if not frontier:
                break
        return frozenset((responses, state) for state, responses in frontier)

    def digest(self) -> str:
        payload = {
            "states": self.states,
            "initial_state": self.initial_state,
            "terminal_states": self.terminal_states,
            "transitions": [
                (t.source, t.request, t.response, t.target, t.observations, t.latency_min_ms, t.latency_max_ms)
                for t in self.transitions
            ],
            "conflicts": self.conflicts,
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ProtocolInferenceReport:
    model: ProtocolModel
    trace_count: int
    request_alphabet: tuple[Message, ...]
    response_alphabet: tuple[Message, ...]
    prefix_states_before_merge: int
    states_after_merge: int
    warnings: tuple[str, ...]


def infer_protocol_model(traces: Iterable[ProtocolTrace], *, merge_equivalent_leaves: bool = True) -> ProtocolInferenceReport:
    trace_list = tuple(traces)
    if not trace_list:
        raise ValueError("at least one protocol trace is required")
    prefix_state: dict[tuple[tuple[Message, Message], ...], State] = {(): "p0"}
    observations: dict[tuple[State, Message, Message, State], list[float]] = defaultdict(list)
    terminal_prefixes: set[tuple[tuple[Message, Message], ...]] = set()
    requests: set[Message] = set()
    responses: set[Message] = set()

    for trace in trace_list:
        prefix: tuple[tuple[Message, Message], ...] = ()
        for step in trace.steps:
            requests.add(step.request)
            responses.add(step.response)
            next_prefix = prefix + ((step.request, step.response),)
            if next_prefix not in prefix_state:
                prefix_state[next_prefix] = f"p{len(prefix_state)}"
            key = (prefix_state[prefix], step.request, step.response, prefix_state[next_prefix])
            observations[key].append(step.latency_ms)
            prefix = next_prefix
        terminal_prefixes.add(prefix)

    aliases = {state: state for state in prefix_state.values()}
    if merge_equivalent_leaves:
        leaves = sorted(prefix_state[prefix] for prefix in terminal_prefixes)
        if leaves:
            canonical = leaves[0]
            for leaf in leaves[1:]:
                aliases[leaf] = canonical

    aggregated: dict[tuple[State, Message, Message, State], list[float]] = defaultdict(list)
    for (source, request, response, target), latencies in observations.items():
        aggregated[(aliases[source], request, response, aliases[target])].extend(latencies)

    transitions = tuple(
        sorted(
            (
                ProtocolTransition(
                    source,
                    request,
                    response,
                    target,
                    observations=len(latencies),
                    latency_min_ms=min(latencies),
                    latency_max_ms=max(latencies),
                )
                for (source, request, response, target), latencies in aggregated.items()
            ),
            key=lambda t: (t.source, t.request, t.response, t.target),
        )
    )
    conflict_map: dict[tuple[State, Message], set[Message]] = defaultdict(set)
    for transition in transitions:
        conflict_map[(transition.source, transition.request)].add(transition.response)
    conflicts = tuple(
        sorted(
            (state, request, tuple(sorted(values)))
            for (state, request), values in conflict_map.items()
            if len(values) > 1
        )
    )
    states = tuple(sorted({aliases[state] for state in prefix_state.values()}))
    terminal_states = tuple(sorted({aliases[prefix_state[prefix]] for prefix in terminal_prefixes}))
    warnings: list[str] = []
    if conflicts:
        warnings.append("Conflicting responses are retained as nondeterminism.")
    if any(not trace.reset_before for trace in trace_list):
        warnings.append("Non-reset traces may contain unmodeled cross-trace state.")
    model = ProtocolModel(states, aliases["p0"], transitions, terminal_states, conflicts)
    return ProtocolInferenceReport(
        model=model,
        trace_count=len(trace_list),
        request_alphabet=tuple(sorted(requests)),
        response_alphabet=tuple(sorted(responses)),
        prefix_states_before_merge=len(prefix_state),
        states_after_merge=len(states),
        warnings=tuple(warnings),
    )


@dataclass(frozen=True, slots=True)
class ProtocolExperiment:
    requests: tuple[Message, ...]
    predicted_partitions: int
    novelty_score: float
    risk: str = "synthetic_only"


def propose_protocol_experiments(
    models: Sequence[ProtocolModel],
    request_alphabet: Sequence[Message],
    *,
    max_depth: int = 4,
    limit: int = 16,
) -> tuple[ProtocolExperiment, ...]:
    if not models:
        return ()
    candidates: list[ProtocolExperiment] = []
    queue = deque([()])
    while queue:
        word = queue.popleft()
        if word:
            predictions = tuple(model.replay(word) for model in models)
            partitions = len(set(predictions))
            novelty = partitions / len(models) - 0.01 * len(word)
            candidates.append(ProtocolExperiment(word, partitions, novelty))
        if len(word) < max_depth:
            queue.extend(word + (symbol,) for symbol in request_alphabet)
    return tuple(sorted(candidates, key=lambda item: (-item.novelty_score, len(item.requests), item.requests))[:limit])
