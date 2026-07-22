"""SoftwareState model for Ω-CS-SOFTWARE-TRUTH."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from .contracts import Contract


@dataclass(frozen=True)
class ExampleCase:
    """One executable behavioral hypothesis for a callable."""

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    expected: Any | None = None
    expect_exception: type[BaseException] | None = None


@dataclass(frozen=True)
class SoftwareState:
    """A callable plus its OAK-verifiable context.

    Canonical tuple:
        SoftwareState = (I, O, A, E, T, R, M)

    where I/O are contracts, A is the algorithm/callable, E is the environment
    note, T are test cases, and R/M are produced by validation as residues and
    memory-positive/memory-negative records.
    """

    name: str
    target: Callable[..., Any]
    contract: Contract
    examples: Sequence[ExampleCase] = field(default_factory=tuple)
    environment: str = "python>=3.10"
    status: str = "B→C"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "contract": self.contract.name,
            "examples": len(self.examples),
            "environment": self.environment,
            "status": self.status,
            "created_at": self.created_at,
        }
