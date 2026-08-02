"""Deterministic Mealy-machine substrate used by the first Ω-RE-T∞ MVP."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from json import dumps
from typing import Iterable, Iterator, Mapping, Sequence

from .models import Observation, ensure_unique

TransitionKey = tuple[int, str]
TransitionValue = tuple[int, str]


@dataclass(frozen=True, slots=True)
class MealyMachine:
    states: tuple[int, ...]
    input_alphabet: tuple[str, ...]
    output_alphabet: tuple[str, ...]
    transitions: Mapping[TransitionKey, TransitionValue]
    initial_state: int = 0
    name: str = "candidate"

    def __post_init__(self) -> None:
        ensure_unique((str(state) for state in self.states), label="states")
        ensure_unique(self.input_alphabet, label="input_alphabet")
        ensure_unique(self.output_alphabet, label="output_alphabet")
        if self.initial_state not in self.states:
            raise ValueError("initial_state must be one of states")
        expected = {(state, symbol) for state in self.states for symbol in self.input_alphabet}
        actual = set(self.transitions)
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            raise ValueError(f"Transition table mismatch; missing={missing}, extra={extra}")
        for key, (next_state, output) in self.transitions.items():
            if key[0] not in self.states or key[1] not in self.input_alphabet:
                raise ValueError(f"Invalid transition key: {key}")
            if next_state not in self.states or output not in self.output_alphabet:
                raise ValueError(f"Invalid transition value: {(next_state, output)}")

    @property
    def candidate_id(self) -> str:
        spec = self.to_spec().copy()
        spec.pop("name", None)
        canonical = dumps(spec, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()[:16]

    @property
    def complexity(self) -> int:
        return len(self.states) * len(self.input_alphabet)

    def reset(self) -> int:
        return self.initial_state

    def step(self, state: int, symbol: str) -> tuple[int, str]:
        try:
            return self.transitions[(state, symbol)]
        except KeyError as error:
            raise ValueError(f"Unsupported state/input pair: {(state, symbol)}") from error

    def run(self, inputs: Sequence[str], *, start_state: int | None = None) -> tuple[tuple[str, ...], int]:
        state = self.initial_state if start_state is None else start_state
        if state not in self.states:
            raise ValueError(f"Unknown start state: {state}")
        outputs: list[str] = []
        for symbol in inputs:
            state, output = self.step(state, symbol)
            outputs.append(output)
        return tuple(outputs), state

    def observe(self, inputs: Sequence[str], *, source: str = "oracle") -> Observation:
        outputs, _ = self.run(inputs)
        return Observation(inputs=tuple(inputs), outputs=outputs, source=source)

    def mismatch_count(self, observations: Iterable[Observation]) -> int:
        mismatches = 0
        for observation in observations:
            predicted, _ = self.run(observation.inputs)
            mismatches += sum(left != right for left, right in zip(predicted, observation.outputs))
        return mismatches

    def is_consistent(self, observations: Iterable[Observation]) -> bool:
        return self.mismatch_count(observations) == 0

    def to_spec(self) -> dict[str, object]:
        transitions = [
            {
                "state": state,
                "input": symbol,
                "next_state": self.transitions[(state, symbol)][0],
                "output": self.transitions[(state, symbol)][1],
            }
            for state in self.states
            for symbol in self.input_alphabet
        ]
        return {
            "name": self.name,
            "states": list(self.states),
            "input_alphabet": list(self.input_alphabet),
            "output_alphabet": list(self.output_alphabet),
            "initial_state": self.initial_state,
            "transitions": transitions,
        }

    @classmethod
    def from_spec(cls, spec: Mapping[str, object]) -> "MealyMachine":
        states = tuple(int(value) for value in spec["states"])  # type: ignore[index]
        inputs = tuple(str(value) for value in spec["input_alphabet"])  # type: ignore[index]
        outputs = tuple(str(value) for value in spec["output_alphabet"])  # type: ignore[index]
        transition_map: dict[TransitionKey, TransitionValue] = {}
        for row in spec["transitions"]:  # type: ignore[index]
            transition_map[(int(row["state"]), str(row["input"]))] = (  # type: ignore[index]
                int(row["next_state"]),  # type: ignore[index]
                str(row["output"]),  # type: ignore[index]
            )
        return cls(
            states=states,
            input_alphabet=inputs,
            output_alphabet=outputs,
            transitions=transition_map,
            initial_state=int(spec.get("initial_state", 0)),
            name=str(spec.get("name", "candidate")),
        )


def enumerate_mealy_machines(
    *,
    state_count: int,
    input_alphabet: Sequence[str],
    output_alphabet: Sequence[str],
    max_candidates: int | None = None,
) -> Iterator[MealyMachine]:
    """Enumerate complete deterministic Mealy machines in canonical table order.

    This exact enumerator is intentionally limited to small research sandboxes.
    The caller must provide a bound when the combinatorial search can grow large.
    """

    if state_count <= 0:
        raise ValueError("state_count must be positive")
    inputs = ensure_unique(input_alphabet, label="input_alphabet")
    outputs = ensure_unique(output_alphabet, label="output_alphabet")
    states = tuple(range(state_count))
    keys = tuple((state, symbol) for state in states for symbol in inputs)
    choices = tuple((next_state, output) for next_state in states for output in outputs)
    total = len(choices) ** len(keys)
    if max_candidates is not None and total > max_candidates:
        raise ValueError(
            f"Search contains {total:,} candidates, exceeding max_candidates={max_candidates:,}"
        )
    for index, assignment in enumerate(product(choices, repeat=len(keys))):
        yield MealyMachine(
            states=states,
            input_alphabet=inputs,
            output_alphabet=outputs,
            transitions=dict(zip(keys, assignment)),
            initial_state=0,
            name=f"fsm-{state_count}s-{index}",
        )


def canonical_demo_machine() -> MealyMachine:
    return MealyMachine(
        states=(0, 1),
        input_alphabet=("A", "B"),
        output_alphabet=("0", "1"),
        transitions={
            (0, "A"): (1, "0"),
            (0, "B"): (0, "1"),
            (1, "A"): (1, "1"),
            (1, "B"): (0, "0"),
        },
        initial_state=0,
        name="canonical-demo-oracle",
    )
