"""Plus-ultra reusable Ω-DE-TensorProd demo."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from omega_vtp_t import (
    PolynomialODE,
    ResidualComponent,
    build_carleman_operator,
    compress_operator_svd,
    conservation_check,
    decompose_residuals,
    entry_from_oak_status,
    invariant_report,
    l2_energy,
    positivity_check,
    select_ode_tensor_degree,
    solve_lifted_linear,
    standard_auxiliary_templates,
    tensor_prod_lift,
)


def main() -> None:
    ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
    samples = np.linspace(-0.5, 0.5, 64).reshape(-1, 1)

    selection = select_ode_tensor_degree(ode, samples, min_degree=1, max_degree=5, max_features=64)
    op = build_carleman_operator(ode, degree=selection.best_degree)
    compressed = compress_operator_svd(op.operator, energy_tol=0.999)

    z0 = tensor_prod_lift([[0.1]], selection.best_degree).features
    traj, solve_report = solve_lifted_linear(z0, op.operator, dt=0.01, steps=5)

    residuals = decompose_residuals(
        [
            ResidualComponent("degree", 1.0 - op.closure_coefficient, 1e-1),
            ResidualComponent("compression", compressed.relative_error, 1e-2),
            ResidualComponent("time", solve_report.residual_norm, 1e-2),
        ]
    )

    before = traj[0, 0]
    after = traj[-1, 0]
    guards = invariant_report(
        [
            conservation_check("constant_feature", before[0], after[0], tolerance=1e-8),
            positivity_check(after, tolerance=1e-8),
        ]
    )

    mminus = entry_from_oak_status(
        "carleman_degree_selection",
        residuals.oak_status,
        evidence=f"worst={residuals.worst_component}",
    )

    print("Ω-DE-TensorProd∞ reusable demo")
    print(f"Selected degree: {selection.best_degree}")
    print(f"Carleman closure: {op.closure_coefficient:.6f}")
    print(f"Low-rank relative error: {compressed.relative_error:.3e}")
    print(f"Solver residual: {solve_report.residual_norm:.3e}")
    print(f"Residual OAK: {residuals.oak_status}, worst={residuals.worst_component}")
    print(f"Invariant OAK: {guards.oak_status}")
    print(f"M-minus entry created: {mminus is not None}")
    print(f"Aux templates: {[template.name for template in standard_auxiliary_templates('x')]}")
    print(f"Final lifted state norm: {l2_energy(after):.3e}")


if __name__ == "__main__":
    main()
