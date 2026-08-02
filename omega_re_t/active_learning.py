"""Bounded active Mealy-machine learning for synthetic or authorized systems.

The learner is deliberately conservative: it discovers a finite behavioral
quotient over a declared input alphabet, probe set and depth.  It never claims
that two access sequences are globally equivalent outside that domain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from itertools import product
from json import dumps
from typing import Callable, Iterable, Mapping, Sequence

Symbol = str
Word = tuple[Symbol, ...]
OutputWord = tuple[Symbol, ...]
MembershipFn = Callable[[Word], OutputWord]


def words(alphabet: Sequence[Symbol], max_length: int, *, include_empty: bool = True) -> tuple[Word, ...]:
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    result: list[Word] = [()] if include_empty else []
    for length in range(1, max_length + 1):
        result.extend(tuple(item) for item in product(alphabet, repeat=length))
    return tuple(result)


@dataclass(slots=True)
class MembershipOracle:
    query_fn: MembershipFn
    cache: dict[Word, OutputWord] = field(default_factory=dict)
    query_count: int = 0

    def query(self, word: Sequence[Symbol]) -> OutputWord:
        key = tuple(word)
        if key not in self.cache:
            output = tuple(self.query_fn(key))
            if len(output) != len(key):
                raise ValueError("A Mealy membership query must return one output per input")
            self.cache[key] = output
            self.query_count += 1
        return self.cache[key]

    def suffix_output(self, prefix: Word, suffix: Word) -> OutputWord:
        full = prefix + suffix
        observed = self.query(full)
        return observed[len(prefix):]


@dataclass(frozen=True, slots=True)
class LearnedTransition:
    source: str
    input_symbol: Symbol
    output_symbol: Symbol
    target: str


@dataclass(frozen=True, slots=True)
class LearnedMealyMachine:
    alphabet: tuple[Symbol, ...]
    states: tuple[str, ...]
    initial_state: str
    transitions: tuple[LearnedTransition, ...]
    domain_max_depth: int
    probe_suffixes: tuple[Word, ...]
    evidence_queries: int

    def _index(self) -> dict[tuple[str, Symbol], LearnedTransition]:
        return {(item.source, item.input_symbol): item for item in self.transitions}

    def run(self, inputs: Sequence[Symbol]) -> OutputWord:
        index = self._index()
        state = self.initial_state
        outputs: list[Symbol] = []
        for symbol in inputs:
            transition = index.get((state, symbol))
            if transition is None:
                raise KeyError(f"No learned transition for state={state!r}, input={symbol!r}")
            outputs.append(transition.output_symbol)
            state = transition.target
        return tuple(outputs)

    def digest(self) -> str:
        payload = {
            "alphabet": self.alphabet,
            "states": self.states,
            "initial_state": self.initial_state,
            "transitions": [
                (t.source, t.input_symbol, t.output_symbol, t.target)
                for t in self.transitions
            ],
            "domain_max_depth": self.domain_max_depth,
            "probe_suffixes": self.probe_suffixes,
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class LearningReport:
    machine: LearnedMealyMachine
    access_sequences: Mapping[str, Word]
    signature_classes: Mapping[str, tuple[Word, ...]]
    tested_words: int
    exact_on_domain: bool
    counterexamples: tuple[Word, ...]
    limitations: tuple[str, ...]


def _signature(oracle: MembershipOracle, access: Word, probes: Sequence[Word]) -> tuple[OutputWord, ...]:
    return tuple(oracle.suffix_output(access, probe) for probe in probes)


def learn_bounded_mealy(
    oracle: MembershipOracle,
    *,
    alphabet: Sequence[Symbol],
    max_access_depth: int = 4,
    max_probe_depth: int = 2,
    validation_depth: int | None = None,
) -> LearningReport:
    """Infer a deterministic behavioral quotient over a bounded domain.

    Access sequences are clustered by their future-output signatures over all
    probe suffixes up to ``max_probe_depth``.  This avoids exhaustive machine
    enumeration while making the finite identification domain explicit.
    """
    alphabet = tuple(dict.fromkeys(alphabet))
    if not alphabet:
        raise ValueError("alphabet cannot be empty")
    if max_access_depth < 0 or max_probe_depth < 1:
        raise ValueError("invalid learning depth")
    probes = words(alphabet, max_probe_depth, include_empty=True)
    accesses = words(alphabet, max_access_depth, include_empty=True)

    signature_to_accesses: dict[tuple[OutputWord, ...], list[Word]] = {}
    for access in accesses:
        signature_to_accesses.setdefault(_signature(oracle, access, probes), []).append(access)

    ordered_classes = sorted(
        signature_to_accesses.items(),
        key=lambda item: (len(item[1][0]), item[1][0], item[0]),
    )
    state_for_signature: dict[tuple[OutputWord, ...], str] = {
        signature: f"q{index}" for index, (signature, _) in enumerate(ordered_classes)
    }
    representative: dict[str, Word] = {
        state_for_signature[signature]: min(members, key=lambda w: (len(w), w))
        for signature, members in ordered_classes
    }

    transitions: list[LearnedTransition] = []
    incomplete: list[tuple[str, Symbol]] = []
    for state, access in representative.items():
        for symbol in alphabet:
            output = oracle.suffix_output(access, (symbol,))[0]
            target_access = access + (symbol,)
            target_signature = _signature(oracle, target_access, probes)
            target = state_for_signature.get(target_signature)
            if target is None:
                # The transition leaves the declared access domain.  Map it by
                # nearest observed signature only when exact; otherwise record
                # incompleteness rather than guessing.
                incomplete.append((state, symbol))
                continue
            transitions.append(LearnedTransition(state, symbol, output, target))

    initial_signature = _signature(oracle, (), probes)
    machine = LearnedMealyMachine(
        alphabet=alphabet,
        states=tuple(sorted(representative)),
        initial_state=state_for_signature[initial_signature],
        transitions=tuple(sorted(transitions, key=lambda t: (t.source, t.input_symbol))),
        domain_max_depth=max_access_depth,
        probe_suffixes=tuple(probes),
        evidence_queries=oracle.query_count,
    )

    check_depth = validation_depth if validation_depth is not None else max_access_depth
    counterexamples: list[Word] = []
    if incomplete:
        counterexamples.extend(representative[state] + (symbol,) for state, symbol in incomplete)
    else:
        for word in words(alphabet, check_depth, include_empty=False):
            if machine.run(word) != oracle.query(word):
                counterexamples.append(word)

    classes = {
        state_for_signature[signature]: tuple(sorted(members, key=lambda w: (len(w), w)))
        for signature, members in ordered_classes
    }
    limitations = (
        "Equivalence is established only over the declared probe suffixes.",
        "Unreachable internal states cannot be reconstructed from black-box queries.",
        "The learner assumes deterministic reset semantics and one output per input.",
    )
    return LearningReport(
        machine=machine,
        access_sequences=representative,
        signature_classes=classes,
        tested_words=len(words(alphabet, check_depth, include_empty=False)),
        exact_on_domain=not counterexamples,
        counterexamples=tuple(counterexamples),
        limitations=limitations,
    )
