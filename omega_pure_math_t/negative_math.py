"""M⁻ registry and finite minimal-hypothesis search."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class NegativeMathEntry:
    hypothesis: str
    counterexample: Any
    failure_reason: str
    repaired_hypothesis: str | None = None
    provenance: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NegativeMathRegistry:
    def __init__(self) -> None:
        self._entries: list[NegativeMathEntry] = []

    def add(self, entry: NegativeMathEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> tuple[NegativeMathEntry, ...]:
        return tuple(self._entries)

    def search(self, text: str) -> tuple[NegativeMathEntry, ...]:
        needle = text.casefold()
        return tuple(
            entry
            for entry in self._entries
            if needle
            in " ".join(
                (
                    entry.hypothesis,
                    entry.failure_reason,
                    entry.repaired_hypothesis or "",
                    entry.provenance or "",
                )
            ).casefold()
        )


def minimal_sufficient_subsets(
    assumptions: Iterable[str],
    proves: Callable[[frozenset[str]], bool],
) -> tuple[frozenset[str], ...]:
    """Exhaustively find inclusion-minimal sufficient subsets.

    This is finite and exact relative to the supplied `proves` oracle.
    It intentionally has no arbitrary fixed search cap.
    """

    names = tuple(dict.fromkeys(assumptions))
    minimal: list[frozenset[str]] = []
    for size in range(len(names) + 1):
        for combo in combinations(names, size):
            candidate = frozenset(combo)
            if any(previous <= candidate for previous in minimal):
                continue
            if proves(candidate):
                minimal.append(candidate)
    return tuple(minimal)
