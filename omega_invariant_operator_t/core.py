"""Invariant-first operator synthesis over bounded finite set-state spaces.

R0.1 is intentionally small and exact.  The engine receives a source state, a
finite universe and named invariants.  It then enumerates state deltas in
increasing symmetric-difference distance.  No domain operator names are part of
its search grammar.

The finite search is a reference oracle for small instances.  It is not a
claim that exhaustive enumeration scales, that the chosen representation is
bias-free, or that a minimal state delta is an optimal optimization heuristic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from itertools import combinations
from typing import Callable, Generic, Hashable, Iterable, Sequence, TypeVar

T = TypeVar("T", bound=Hashable)
State = frozenset[T]


def _stable(items: Iterable[T]) -> tuple[T, ...]:
    """Return a deterministic ordering without requiring comparable elements."""

    return tuple(sorted(items, key=repr))


@dataclass(frozen=True, slots=True)
class NamedInvariant(Generic[T]):
    name: str
    predicate: Callable[[State[T]], bool]
    description: str = ""

    def holds(self, state: State[T]) -> bool:
        return bool(self.predicate(state))


@dataclass(frozen=True, slots=True)
class InvariantCheck:
    passed: tuple[str, ...]
    failed: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.failed


@dataclass(frozen=True, slots=True)
class SearchBiasLedger:
    """All R0.1 search preferences that could otherwise become hidden heuristics."""

    representation: str = "finite_set_state"
    objective: str = "minimum_nonidentity_symmetric_difference"
    enumeration: str = "complete_distance_shells"
    tie_break: str = "repr_lexicographic"
    backend: str = "exact_shell_enumeration"
    operator_library: tuple[str, ...] = ()
    grammar_primitives: tuple[str, ...] = ("remove_element", "add_element")
    caveat: str = (
        "zero hidden heuristic, not zero inductive bias: representation, objective, "
        "grammar, ordering and budget are explicit and auditable"
    )


@dataclass(frozen=True, slots=True)
class OperatorWitness(Generic[T]):
    removed: tuple[T, ...]
    added: tuple[T, ...]
    target: State[T]
    invariant_check: InvariantCheck

    @property
    def symmetric_difference(self) -> int:
        return len(self.removed) + len(self.added)

    @property
    def exchange_signature(self) -> tuple[int, int]:
        return (len(self.removed), len(self.added))


@dataclass(frozen=True, slots=True)
class SynthesisReceipt(Generic[T]):
    status: str
    source: State[T]
    universe_size: int
    candidates_examined: int
    shells_completed: int
    minimal_distance: int | None
    witnesses: tuple[OperatorWitness[T], ...]
    finite_minimality_certified: bool
    budget_exhausted: bool
    max_candidates: int
    max_witnesses: int
    bias: SearchBiasLedger
    oak_boundaries: tuple[str, ...] = (
        "finite minimal delta != best optimization move",
        "invariant preservation != objective improvement",
        "exact bounded search != scalable synthesis",
        "explicit bias ledger != absence of inductive bias",
        "receipt PASS != empirical superiority",
    )
    theorem_claimed: bool = False
    automatic_apoptosis: bool = False

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)


def _jsonable(value):
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, frozenset):
        return [_jsonable(item) for item in _stable(value)]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def check_invariants(state: State[T], invariants: Sequence[NamedInvariant[T]]) -> InvariantCheck:
    passed: list[str] = []
    failed: list[str] = []
    for invariant in invariants:
        (passed if invariant.holds(state) else failed).append(invariant.name)
    return InvariantCheck(tuple(passed), tuple(failed))


def apply_witness(source: State[T], witness: OperatorWitness[T]) -> State[T]:
    return frozenset((source - frozenset(witness.removed)) | frozenset(witness.added))


def synthesize_minimal_operator(
    source: Iterable[T],
    universe: Iterable[T],
    invariants: Sequence[NamedInvariant[T]],
    *,
    max_candidates: int = 100_000,
    max_witnesses: int = 64,
    bias: SearchBiasLedger | None = None,
) -> SynthesisReceipt[T]:
    """Find exact minimal non-identity invariant-preserving deltas when bounded.

    The search walks complete symmetric-difference shells in increasing distance.
    Once a shell contains valid targets, completing that shell is sufficient to
    certify minimality *within the declared finite universe and invariants*.
    If the candidate budget is exhausted before the required shell is complete,
    the receipt is HOLD and no minimality certificate is issued.
    """

    if max_candidates <= 0:
        raise ValueError("max_candidates must be positive")
    if max_witnesses <= 0:
        raise ValueError("max_witnesses must be positive")
    if not invariants:
        raise ValueError("at least one invariant is required")

    source_state = frozenset(source)
    universe_state = frozenset(universe)
    if not source_state <= universe_state:
        raise ValueError("source must be a subset of universe")
    source_check = check_invariants(source_state, invariants)
    if not source_check.ok:
        raise ValueError(f"source violates invariants: {source_check.failed}")

    ordered_source = _stable(source_state)
    ordered_outside = _stable(universe_state - source_state)
    bias = bias or SearchBiasLedger()
    examined = 0
    shells_completed = 0

    for distance in range(1, len(universe_state) + 1):
        shell_witnesses: list[OperatorWitness[T]] = []
        min_removed = max(0, distance - len(ordered_outside))
        max_removed = min(distance, len(ordered_source))

        for removed_count in range(min_removed, max_removed + 1):
            added_count = distance - removed_count
            if added_count > len(ordered_outside):
                continue
            for removed in combinations(ordered_source, removed_count):
                removed_set = frozenset(removed)
                for added in combinations(ordered_outside, added_count):
                    if examined >= max_candidates:
                        return SynthesisReceipt(
                            status="HOLD",
                            source=source_state,
                            universe_size=len(universe_state),
                            candidates_examined=examined,
                            shells_completed=shells_completed,
                            minimal_distance=None,
                            witnesses=(),
                            finite_minimality_certified=False,
                            budget_exhausted=True,
                            max_candidates=max_candidates,
                            max_witnesses=max_witnesses,
                            bias=bias,
                        )
                    examined += 1
                    target = frozenset((source_state - removed_set) | frozenset(added))
                    if target == source_state:
                        continue
                    report = check_invariants(target, invariants)
                    if report.ok:
                        shell_witnesses.append(
                            OperatorWitness(
                                removed=_stable(removed),
                                added=_stable(added),
                                target=target,
                                invariant_check=report,
                            )
                        )

        shells_completed += 1
        if shell_witnesses:
            ordered = tuple(
                sorted(
                    shell_witnesses,
                    key=lambda witness: (
                        tuple(map(repr, witness.removed)),
                        tuple(map(repr, witness.added)),
                    ),
                )[:max_witnesses]
            )
            return SynthesisReceipt(
                status="PASS",
                source=source_state,
                universe_size=len(universe_state),
                candidates_examined=examined,
                shells_completed=shells_completed,
                minimal_distance=distance,
                witnesses=ordered,
                finite_minimality_certified=True,
                budget_exhausted=False,
                max_candidates=max_candidates,
                max_witnesses=max_witnesses,
                bias=bias,
            )

    return SynthesisReceipt(
        status="HOLD",
        source=source_state,
        universe_size=len(universe_state),
        candidates_examined=examined,
        shells_completed=shells_completed,
        minimal_distance=None,
        witnesses=(),
        finite_minimality_certified=True,
        budget_exhausted=False,
        max_candidates=max_candidates,
        max_witnesses=max_witnesses,
        bias=bias,
    )
