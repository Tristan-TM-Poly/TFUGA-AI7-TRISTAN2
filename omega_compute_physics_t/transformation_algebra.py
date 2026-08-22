"""Composable optimization transformation algebra for R0.7.

Transformations are planning objects. Applying one to source code is a separate,
reviewed engineering action and requires measurement against a baseline.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OptimizationTransformation:
    transformation_id: str
    family: str
    preconditions: tuple[str, ...]
    expected_effects: tuple[str, ...]
    risks: tuple[str, ...] = ()
    composable: bool = True
    status: str = "optimization-transformation-spec"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TransformationProgram:
    transformations: tuple[OptimizationTransformation, ...]
    families: tuple[str, ...]
    risk_union: tuple[str, ...]
    status: str = "optimization-transformation-program"
    oak_warning: str = (
        "A transformation program is a hypothesis about a source rewrite. It "
        "is not evidence of correctness, speedup, or semantic preservation."
    )

    def ids(self) -> tuple[str, ...]:
        return tuple(row.transformation_id for row in self.transformations)


def canonical_transformation_library() -> tuple[OptimizationTransformation, ...]:
    return (
        OptimizationTransformation("preallocate", "memory", ("repeated-allocation",), ("fewer-allocations",)),
        OptimizationTransformation("reuse-buffer", "memory", ("mutable-buffer-safe",), ("fewer-allocations",)),
        OptimizationTransformation("eliminate-copy", "memory", ("copy-observed",), ("fewer-bytes-moved",)),
        OptimizationTransformation("layout-reorder", "locality", ("layout-flexible",), ("better-locality",)),
        OptimizationTransformation("loop-fusion", "locality", ("compatible-loops",), ("fewer-passes",)),
        OptimizationTransformation("loop-tiling", "locality", ("regular-index-space",), ("cache-locality",)),
        OptimizationTransformation("vectorize", "compute", ("data-parallel",), ("higher-throughput",), ("numerical-order-change",)),
        OptimizationTransformation("batch", "compute", ("batchable-calls",), ("lower-call-overhead",)),
        OptimizationTransformation("parallelize", "parallel", ("independent-work",), ("lower-wall-time",), ("synchronization-overhead",)),
        OptimizationTransformation("memoize", "algorithmic", ("repeatable-pure-subproblem",), ("avoid-recomputation",), ("memory-growth",)),
        OptimizationTransformation("sparsify", "representation", ("sparse-structure",), ("less-work",), ("representation-overhead",)),
        OptimizationTransformation("change-algorithm", "algorithmic", ("equivalent-specification",), ("lower-computational-work",), ("semantic-risk",)),
    )


def compose_transformations(
    transformations: Sequence[OptimizationTransformation],
    *,
    allow_duplicates: bool = False,
) -> TransformationProgram:
    rows = tuple(transformations)
    if not rows:
        raise ValueError("at least one transformation is required")
    if not all(row.composable for row in rows):
        raise ValueError("program contains a non-composable transformation")
    ids = [row.transformation_id for row in rows]
    if not allow_duplicates and len(ids) != len(set(ids)):
        raise ValueError("duplicate transformations require allow_duplicates=True")
    return TransformationProgram(
        transformations=rows,
        families=tuple(sorted({row.family for row in rows})),
        risk_union=tuple(sorted({risk for row in rows for risk in row.risks})),
    )
