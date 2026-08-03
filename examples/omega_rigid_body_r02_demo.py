"""Executable Ω-RIGID-BODY-T R0.2 demonstration."""
from __future__ import annotations

import json

from omega_rigid_body_t.r02 import (
    PrincipalMoments,
    exact_parameters_from_state,
    phase_closure_report,
    run_oak_benchmarks,
)


def main() -> None:
    model = PrincipalMoments(1.0, 2.0, 3.0)
    parameters = exact_parameters_from_state(model, (-0.2, -0.3, 1.0))
    phase = phase_closure_report(model, parameters, samples=2048)
    payload = {
        "exact_branch": parameters.to_dict(),
        "rotation_of_rotation": phase.to_dict(),
        "oak": run_oak_benchmarks().to_dict(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
