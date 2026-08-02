"""Partial and nondeterministic finite-state reconstruction primitives."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Mapping, Sequence

Symbol = str
State = str


@dataclass(frozen=True, slots=True)
class NDTransition:
    source: State
    input_symbol: Symbol
    output_symbol: Symbol
    target: State


@dataclass(frozen=True, slots=True)
class NondeterministicMealyMachine:
    states: tuple[State, ...]
    alphabet: tuple[Symbol, ...]
    outputs: tuple[Symbol, ...]
    initial_states: tuple[State, ...]
    transitions: tuple[NDTransition, ...]

    def __post_init__(self) -> None:
        state_set = set(self.states)
        if not self.states or not self.initial_states:
            raise ValueError("states and initial_states cannot be empty")
        if not set(self.initial_states) <= state_set:
            raise ValueError("initial_states must belong to states")
        if len(state_set) != len(self.states):
            raise ValueError("states must be unique")
        for transition in self.transitions:
            if transition.source not in state_set or transition.target not in state_set:
                raise ValueError("transition references unknown state")
            if transition.input_symbol not in self.alphabet:
                raise ValueError("transition references unknown input")
            if transition.output_symbol not in self.outputs:
                raise ValueError("transition references unknown output")

    def index(self) -> Mapping[tuple[State, Symbol], tuple[NDTransition, ...]]:
        buckets: dict[tuple[State, Symbol], list[NDTransition]] = defaultdict(list)
        for transition in self.transitions:
            buckets[(transition.source, transition.input_symbol)].append(transition)
        return {key: tuple(value) for key, value in buckets.items()}

    def traces(self, inputs: Sequence[Symbol]) -> frozenset[tuple[tuple[Symbol, ...], State]]:
        index = self.index()
        frontier: set[tuple[State, tuple[Symbol, ...]]] = {
            (state, ()) for state in self.initial_states
        }
        for symbol in inputs:
            next_frontier: set[tuple[State, tuple[Symbol, ...]]] = set()
            for state, emitted in frontier:
                for transition in index.get((state, symbol), ()):
                    next_frontier.add((transition.target, emitted + (transition.output_symbol,)))
            frontier = next_frontier
            if not frontier:
                break
        return frozenset((emitted, state) for state, emitted in frontier)

    def accepted_output_words(self, inputs: Sequence[Symbol]) -> frozenset[tuple[Symbol, ...]]:
        return frozenset(outputs for outputs, _ in self.traces(inputs))

    def reachable_states(self, max_depth: int = 8) -> frozenset[State]:
        index = self.index()
        seen = set(self.initial_states)
        queue = deque((state, 0) for state in self.initial_states)
        while queue:
            state, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for symbol in self.alphabet:
                for transition in index.get((state, symbol), ()):
                    if transition.target not in seen:
                        seen.add(transition.target)
                        queue.append((transition.target, depth + 1))
        return frozenset(seen)

    def determinism_violations(self) -> tuple[tuple[State, Symbol, int], ...]:
        index = self.index()
        return tuple(
            sorted(
                (state, symbol, len(items))
                for (state, symbol), items in index.items()
                if len(items) > 1
            )
        )


@dataclass(frozen=True, slots=True)
class BoundedEquivalenceReport:
    equivalent: bool
    tested_words: int
    counterexamples: tuple[tuple[Symbol, ...], ...]
    domain_depth: int


def bounded_trace_equivalence(
    left: NondeterministicMealyMachine,
    right: NondeterministicMealyMachine,
    *,
    max_depth: int,
) -> BoundedEquivalenceReport:
    if left.alphabet != right.alphabet:
        raise ValueError("alphabets must match")
    counterexamples: list[tuple[Symbol, ...]] = []
    tested = 0
    for length in range(max_depth + 1):
        for word in product(left.alphabet, repeat=length):
            tested += 1
            if left.accepted_output_words(word) != right.accepted_output_words(word):
                counterexamples.append(tuple(word))
    return BoundedEquivalenceReport(
        equivalent=not counterexamples,
        tested_words=tested,
        counterexamples=tuple(counterexamples),
        domain_depth=max_depth,
    )


def infer_prefix_tree_transducer(
    traces: Iterable[tuple[Sequence[Symbol], Sequence[Symbol]]],
) -> NondeterministicMealyMachine:
    """Build an exact prefix-tree transducer from finite observations.

    Conflicting outputs for the same prefix/input are retained as explicit
    nondeterminism instead of being silently resolved.
    """
    states = {"q0"}
    transitions: set[NDTransition] = set()
    alphabet: set[Symbol] = set()
    outputs: set[Symbol] = set()
    state_for_prefix: dict[tuple[Symbol, ...], State] = {(): "q0"}

    for raw_inputs, raw_outputs in traces:
        inputs = tuple(raw_inputs)
        emitted = tuple(raw_outputs)
        if len(inputs) != len(emitted):
            raise ValueError("trace inputs and outputs must have equal lengths")
        prefix: tuple[Symbol, ...] = ()
        for symbol, output in zip(inputs, emitted):
            alphabet.add(symbol)
            outputs.add(output)
            next_prefix = prefix + (symbol,)
            if next_prefix not in state_for_prefix:
                state_for_prefix[next_prefix] = f"q{len(state_for_prefix)}"
                states.add(state_for_prefix[next_prefix])
            transitions.add(
                NDTransition(
                    state_for_prefix[prefix],
                    symbol,
                    output,
                    state_for_prefix[next_prefix],
                )
            )
            prefix = next_prefix

    return NondeterministicMealyMachine(
        states=tuple(sorted(states)),
        alphabet=tuple(sorted(alphabet)),
        outputs=tuple(sorted(outputs)),
        initial_states=("q0",),
        transitions=tuple(sorted(transitions, key=lambda t: (t.source, t.input_symbol, t.output_symbol, t.target))),
    )
