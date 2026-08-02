"""Adapters from Ω-NARUTO-HMAGFM-HGFMnD² into repository-wide organs.

The M-minus packets intentionally mirror ``omega_prof_poly_t.mminus_registry``
without importing the large umbrella package at module import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import OAKMergeResult, proposal_score


@dataclass(frozen=True)
class MMinusExportEntry:
    error: str
    rule: str
    fix: str
    status: str


@dataclass(frozen=True)
class MMinusExportRegistry:
    entries: tuple[MMinusExportEntry, ...]
    next_action: str


def to_claim_packet(result: OAKMergeResult) -> dict[str, Any] | None:
    """Convert the accepted proposal to a generic claim packet.

    The packet is intentionally conservative: selection is not certification.
    """

    accepted = result.accepted
    if accepted is None:
        return None
    return {
        "claim_id": accepted.proposal_id,
        "agent_id": accepted.agent_id,
        "claim": accepted.conclusion,
        "hypothesis": accepted.hypothesis,
        "status": accepted.status.name,
        "local_oak_score": proposal_score(accepted),
        "evidence": list(accepted.evidence),
        "counterevidence": list(accepted.counterevidence),
        "provenance": list(accepted.provenance),
        "uncertainty": accepted.uncertainty,
        "non_claim": "OAKMerge selection is not external validation or certification.",
        "next_experiment": result.next_experiment,
    }


def to_mminus_registry(result: OAKMergeResult) -> MMinusExportRegistry:
    """Preserve rejected clones in the repository M-minus field shape."""

    entries = tuple(
        MMinusExportEntry(
            error=f"proposal {item.proposal_id} was not selected: {item.reason}",
            rule="retain rejected conclusions as falsification memory",
            fix=(
                "add stronger provenance/evidence, lower risk, reduce resource "
                "cost, or run the discriminating experiment"
            ),
            status="observed",
        )
        for item in result.rejected
    )
    return MMinusExportRegistry(
        entries=entries,
        next_action=result.next_experiment or "review_retained_residues",
    )
