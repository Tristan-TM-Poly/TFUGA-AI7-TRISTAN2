"""Ω-VTP-T++ v2 demo: Chebyshev, Koopman, closure, train/test OAK, CVCD."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from omega_vtp_t import (
    chebyshev_lift,
    closure_residual,
    fit_koopman_tensorprod,
    select_cvcd_features,
    tensor_prod_lift,
    train_test_koopman_oak,
)


def main() -> None:
    x = np.linspace(-1, 1, 128).reshape(-1, 1)
    y = 0.5 * x

    cheb = chebyshev_lift(x, 4, domain=([-1.0], [1.0]))
    koopman = fit_koopman_tensorprod(x, y, degree=4, lift="monomial")
    closure = closure_residual(x, y, degree=4)
    oak = train_test_koopman_oak(x, y, degree=4, lift="monomial", seed=7)

    rng = np.random.default_rng(0)
    samples = rng.normal(size=(256, 2))
    target = 3 * samples[:, 0] ** 2 + 0.05 * rng.normal(size=256)
    lift = tensor_prod_lift(samples, degree=2)
    selection = select_cvcd_features(lift, target, top_k=4)

    print("Ω-VTP-T++ v2 demo")
    print(f"Chebyshev features: {cheb.features.shape[1]}")
    print(f"Koopman residual: {koopman.fit.report.relative_residual:.3e}")
    print(f"Closure coefficient: {closure.closure_coefficient:.12f}")
    print(f"Train/test OAK status: {oak.score.oak_status}")
    print(f"Train/test residual: {oak.test_relative_residual:.3e}")
    print(f"CVCD selected alphas: {selection.alphas}")


if __name__ == "__main__":
    main()
