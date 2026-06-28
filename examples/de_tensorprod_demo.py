"""Ω-DE-TensorProd demo for EDO/EDP prototypes."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from omega_vtp_t import (
    PolynomialODE,
    build_carleman_operator,
    carleman_residual_on_samples,
    burgers_rhs_periodic,
    mass,
    pde_residual_euler,
    reaction_diffusion_rhs,
)


def main() -> None:
    ode = PolynomialODE(dimension=1, coefficients=({(1,): 0.7, (2,): 0.1},))
    op = build_carleman_operator(ode, degree=4)
    samples = np.linspace(-0.5, 0.5, 64).reshape(-1, 1)
    ode_report = carleman_residual_on_samples(ode, samples, degree=4)

    x = np.linspace(0, 2 * np.pi, 128, endpoint=False)
    dx = x[1] - x[0]
    dt = 1e-3
    u = np.sin(x)
    rd_rhs = reaction_diffusion_rhs(u, dx=dx, diffusion=0.05, reaction=lambda z: z - z**3)
    burgers_rhs = burgers_rhs_periodic(u, dx=dx, viscosity=0.02)
    u_next = u + dt * burgers_rhs
    pde_report = pde_residual_euler(u, u_next, dt=dt, rhs_now=burgers_rhs, dx=dx)

    print("Ω-DE-TensorProd demo")
    print(f"Carleman feature count: {len(op.alphas)}")
    print(f"Carleman closure coefficient: {op.closure_coefficient:.6f}")
    print(f"Carleman sample residual: {ode_report['sample_relative_residual']:.3e}")
    print(f"Reaction-diffusion RHS norm: {np.linalg.norm(rd_rhs):.3e}")
    print(f"Initial mass: {mass(u, dx):.3e}")
    print(f"PDE Euler residual: {pde_report.relative_residual:.3e}")
    print(f"PDE OAK status: {pde_report.oak_status}")


if __name__ == "__main__":
    main()
