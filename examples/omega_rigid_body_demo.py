from __future__ import annotations

import json

from omega_rigid_body_t import (
    Invariants,
    PrincipalInertia,
    analytic_omega,
    elliptic_parameters,
    run_oak_benchmarks,
)


def main() -> None:
    inertia = PrincipalInertia(1.0, 2.0, 3.0)
    invariants = Invariants(energy=1.8, angular_momentum_squared=9.0)
    parameters = elliptic_parameters(inertia, invariants)
    times = [parameters.period * index / 8.0 for index in range(9)]
    payload = {
        "inertia": inertia.to_dict(),
        "invariants": invariants.to_dict(),
        "parameters": parameters.to_dict(),
        "samples": [{"time": time, "omega": analytic_omega(time, parameters)} for time in times],
        "oak": run_oak_benchmarks().to_dict(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
