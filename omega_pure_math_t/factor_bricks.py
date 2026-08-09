"""Relative factorization by an explicit brick language."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import Iterable


@dataclass(frozen=True)
class FactorizationWitness:
    object_name: str
    bricks: tuple[str, ...]
    operation: str = "⊗"

    @property
    def length(self) -> int:
        return len(self.bricks)

    @property
    def expression(self) -> str:
        if not self.bricks:
            return "1"
        return f" {self.operation} ".join(self.bricks)


@dataclass
class BrickLanguage:
    """Finite witness registry for a chosen factorization language B."""

    name: str
    witnesses: dict[str, list[FactorizationWitness]] = field(default_factory=dict)

    def add(self, witness: FactorizationWitness) -> None:
        self.witnesses.setdefault(witness.object_name, []).append(witness)

    def minimum_length(self, object_name: str) -> float:
        candidates = self.witnesses.get(object_name, ())
        if not candidates:
            return inf
        return float(min(item.length for item in candidates))

    def irreducible(self, object_name: str) -> bool:
        """Recorded relative irreducibility in the declared brick language.

        The object must be explicitly admitted as a one-brick witness and no
        nontrivial (length >=2) factorization may be recorded. Unknown objects
        are never promoted to irreducible merely because search found nothing.
        This is an evidence-state predicate, not a theorem that no unrecorded
        factorization exists.
        """

        candidates = self.witnesses.get(object_name)
        if not candidates:
            return False
        admitted_as_brick = any(item.length == 1 for item in candidates)
        has_nontrivial_factorization = any(item.length >= 2 for item in candidates)
        return admitted_as_brick and not has_nontrivial_factorization


def compose_witnesses(
    left: FactorizationWitness,
    right: FactorizationWitness,
    *,
    composite_name: str,
    operation: str = "⊗",
) -> FactorizationWitness:
    """Concatenate witnesses, yielding the constructive proof behind T1."""

    return FactorizationWitness(
        object_name=composite_name,
        bricks=left.bricks + right.bricks,
        operation=operation,
    )


def subadditivity_certificate(
    left: FactorizationWitness,
    right: FactorizationWitness,
    composite: FactorizationWitness,
) -> bool:
    """Verify len(composite) <= len(left)+len(right)."""

    return composite.length <= left.length + right.length


def minimum_recorded_length(witnesses: Iterable[FactorizationWitness]) -> float:
    values = tuple(witnesses)
    return float(min((w.length for w in values), default=inf))
