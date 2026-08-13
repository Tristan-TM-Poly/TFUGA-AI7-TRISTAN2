from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MathArtifactKind = Literal[
    "definition",
    "axiom",
    "notation",
    "example",
    "theorem",
    "lemma",
    "corollary",
    "proof",
    "counterexample",
    "exercise",
    "solution",
    "algorithm",
    "heuristic",
]


@dataclass(frozen=True, slots=True)
class SourceAnchor:
    """Provenance pointer for one extracted mathematical object.

    `source_url` identifies where the source came from; `page`/`bbox` may be
    absent when the source format does not expose them.  A SourceAnchor is
    provenance, not a truth certificate.
    """

    source_id: str
    source_url: str
    document_sha256: str | None = None
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    license_status: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProofGenome:
    """Structural signature of a proof candidate.

    The genome is intentionally representation-oriented.  Similar genomes may
    suggest reusable proof structure, but similarity never certifies validity.
    """

    quantifier_signature: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    representations: tuple[str, ...] = ()
    operators: tuple[str, ...] = ()
    lemmas: tuple[str, ...] = ()
    branching_signature: tuple[int, ...] = ()
    kernel_status: Literal["unverified", "accepted", "rejected"] = "unverified"


@dataclass(frozen=True, slots=True)
class MathArtifact:
    """Atomic mathematics object with semantic and provenance boundaries."""

    artifact_id: str
    kind: MathArtifactKind
    natural_text: str
    normalized_statement: str | None = None
    formal_statement: str | None = None
    assumptions: tuple[str, ...] = ()
    conclusion: str | None = None
    definitions_used: tuple[str, ...] = ()
    proof_genome: ProofGenome | None = None
    source_anchors: tuple[SourceAnchor, ...] = ()
    semantic_residual: float | None = None
    formal_status: Literal[
        "unformalized", "candidate", "compiled", "kernel_accepted", "kernel_rejected"
    ] = "unformalized"
    oak_status: Literal["source_extracted", "hold", "verified", "rejected"] = "source_extracted"

    def is_formally_verified(self) -> bool:
        return self.formal_status == "kernel_accepted"

    def is_oak_verified(self) -> bool:
        return self.oak_status == "verified"
