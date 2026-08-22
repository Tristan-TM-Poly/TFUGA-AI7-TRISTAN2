from __future__ import annotations

from omega_capability_os_t.core import Capability


def resource_arbitration_capability() -> Capability:
    """Expose MACT's distinct resource-arbitration behavior through Capability OS.

    This is an interoperability contract, not a second capability ontology and not
    authority to execute any selected transformation. MACT remains planning-only.
    """

    return Capability(
        capability_id="mact-resource-arbitration",
        domains=("planning", "optimization", "resource-arbitrage"),
        consumes=("candidate_set", "verification_contract", "resource_vector"),
        produces=("eligible_pareto_front", "planning_receipt", "residual"),
        authority="read",
        quality=0.9,
        information_gain=0.8,
        verifiability=0.9,
        reuse=0.9,
        cost=0.2,
        latency=0.2,
        risk=0.1,
    )
