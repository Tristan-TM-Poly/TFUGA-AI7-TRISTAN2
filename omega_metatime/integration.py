from __future__ import annotations

from omega_capability_os_t.core import Capability


def temporal_measurement_capability() -> Capability:
    """Expose MetaTime's distinct temporal measurement/controller surface.

    The contract is read-only and carries no authority to execute the selected
    regime, open branches, automate actions, or promote claims.
    """

    return Capability(
        capability_id="metatime-temporal-measurement",
        domains=("temporal-analysis", "planning", "learning"),
        consumes=("temporal_state", "capability_delta", "evidence"),
        produces=("temporal_regime", "temporal_metrics", "residual"),
        authority="read",
        quality=0.9,
        information_gain=0.9,
        verifiability=0.9,
        reuse=0.85,
        cost=0.2,
        latency=0.1,
        risk=0.05,
    )
