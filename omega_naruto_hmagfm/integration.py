"""Adapters from Ω-NARUTO-HMAGFM-HGFMnD² into repository-wide organs."""

from __future__ import annotations

from typing import Any

from omega_prof_poly_t.mminus_registry import (
    MMinusEntry,
    MMinusRegistry,
)

from .core import OAKMergeResult, proposal_score


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


def to_mminus_registry(result: OAKMergeResult) -> MMinusRegistry:
    """Preserve every rejected clone result in the shared M-minus shape."""

    entries = tuple(
        MMinusEntry(
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
    return MMinusRegistry(
        entries=entries,
        next_action=result.next_experiment or "review_retained_residues",
    )
