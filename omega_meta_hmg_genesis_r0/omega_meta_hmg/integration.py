from __future__ import annotations

from omega_capability_os_t.core import Capability


def hmg_representation_research_capability() -> Capability:
    """Expose the HMG-specific representation/provenance research surface.

    Generic capability, authority, replay, and cross-skill promotion remain owned by
    the root Capability OS. This contract is read-only and grants no execution or
    external-write authority.
    """

    return Capability(
        capability_id="hmg-representation-research",
        domains=("hypergraph", "representation-search", "provenance"),
        consumes=("residuals", "representation_candidates", "evidence"),
        produces=("tournament_report", "provenance_manifest", "residual"),
        authority="read",
        quality=0.8,
        information_gain=0.9,
        verifiability=0.85,
        reuse=0.8,
        cost=0.3,
        latency=0.2,
        risk=0.1,
    )
