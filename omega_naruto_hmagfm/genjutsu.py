"""Deterministic Genjutsu red-team checks.

These checks flag common ways a proposal can look convincing while remaining
unsupported, circular, private, or epistemically inflated. They are linting
heuristics, not a substitute for expert review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class AuditableProposal(Protocol):
    hypothesis: str
    conclusion: str
    status: int
    confidence: float
    uncertainty: float
    evidence: Sequence[str]
    provenance: Sequence[str]


class GenjutsuCode(str, Enum):
    FABRICATED_SOURCE_MARKER = "FABRICATED_SOURCE_MARKER"
    CIRCULAR_EVIDENCE = "CIRCULAR_EVIDENCE"
    PRIVATE_SOURCE_MARKER = "PRIVATE_SOURCE_MARKER"
    STATUS_INFLATION = "STATUS_INFLATION"
    UNTRACEABLE = "UNTRACEABLE"
    CERTAINTY_MISMATCH = "CERTAINTY_MISMATCH"


@dataclass(frozen=True)
class GenjutsuFinding:
    code: GenjutsuCode
    severity: str
    message: str


_FABRICATED_MARKERS = ("invented", "fabricated", "placeholder", "fake-source")
_PRIVATE_MARKERS = ("private", "restricted", "secret", "birth-date", "dob")


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def audit_proposal(proposal: AuditableProposal) -> tuple[GenjutsuFinding, ...]:
    """Return deterministic adversarial findings for one proposal."""

    findings: list[GenjutsuFinding] = []
    evidence = tuple(_normalize(item) for item in proposal.evidence)
    provenance = tuple(_normalize(item) for item in proposal.provenance)
    conclusion = _normalize(proposal.conclusion)
    hypothesis = _normalize(proposal.hypothesis)
    sources = evidence + provenance

    if any(marker in source for marker in _FABRICATED_MARKERS for source in sources):
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.FABRICATED_SOURCE_MARKER,
                "P0",
                "source metadata contains a fabricated or placeholder marker",
            )
        )

    if conclusion in evidence or hypothesis in evidence:
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.CIRCULAR_EVIDENCE,
                "P1",
                "the claim text itself is being used as evidence",
            )
        )

    if any(marker in source for marker in _PRIVATE_MARKERS for source in sources):
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.PRIVATE_SOURCE_MARKER,
                "P0",
                "source metadata indicates private or restricted material",
            )
        )

    if int(proposal.status) >= 6 and len(proposal.evidence) < 2:
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.STATUS_INFLATION,
                "P1",
                "benchmark-or-higher status requires at least two evidence artifacts",
            )
        )

    if not proposal.provenance:
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.UNTRACEABLE,
                "P1",
                "no provenance was supplied",
            )
        )

    if proposal.confidence > 0.90 and proposal.uncertainty > 0.40:
        findings.append(
            GenjutsuFinding(
                GenjutsuCode.CERTAINTY_MISMATCH,
                "P1",
                "high confidence conflicts with high stated uncertainty",
            )
        )

    return tuple(findings)


def has_blocking_finding(findings: Sequence[GenjutsuFinding]) -> bool:
    return any(finding.severity == "P0" for finding in findings)
