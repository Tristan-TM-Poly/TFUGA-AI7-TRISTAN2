"""Residue Miner for Tristan CanonOS.

Converts unexplained residue into cautious hypotheses and next tests. Residue is
fertile, not automatically true.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResidueStatus(StrEnum):
    RAW = "raw"
    PATTERN = "pattern"
    HYPOTHESIS = "hypothesis"
    TESTABLE = "testable"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class ResiduePacket:
    residue: str
    status: ResidueStatus
    candidate_pattern: str
    hypothesis: str
    safe_next_action: str


def mine_residue(residue: str, *, sensitive: bool = False, has_pattern: bool = False) -> ResiduePacket:
    if sensitive:
        return ResiduePacket(
            residue,
            ResidueStatus.QUARANTINED,
            "sensitive residue cannot be public pattern-mined yet",
            "quarantined until privacy/IP/OAK review",
            "Keep private; run Privacy/IP/OAK gates.",
        )

    if has_pattern:
        return ResiduePacket(
            residue,
            ResidueStatus.TESTABLE,
            f"Repeated pattern detected in residue: {residue}",
            f"Hypothesis: this residue may indicate a missing mechanism or missing branch around {residue}.",
            "Create a falsifiable test or minimal artifact.",
        )

    return ResiduePacket(
        residue,
        ResidueStatus.RAW,
        "no stable pattern yet",
        "hypothesis not ready",
        "Collect more examples and avoid overclaiming.",
    )
