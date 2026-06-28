"""Run a minimal Ω-VTP-T++ TensorProd-Lift demo.

Usage:
    python examples/tensorprod_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from omega_vtp_t import polynomial_eval_from_lift, tensor_prod_lift
from omega_vtp_t.oakbench_vtp import (
    oak_dynamic_lift_demo,
    oak_polynomial_exactness_demo,
    oak_speed_memory_demo,
)


def main() -> None:
    v = np.array([[2.0, 3.0]])
    coeffs = {
        (0, 0): 2.0,
        (2, 0): 3.0,
        (1, 1): 5.0,
        (0, 3): -7.0,
    }

    lift = tensor_prod_lift(v, degree=3)
    value = polynomial_eval_from_lift(v, degree=3, coeffs=coeffs)

    print("Ω-VTP-T++ TensorProd-Lift")
    print(f"features: {lift.features.shape[1]}")
    print(f"F(2, 3) = {value[0]}")
    print("OAK polynomial:", oak_polynomial_exactness_demo())
    print("OAK dynamic:", oak_dynamic_lift_demo(degree=4))
    print("OAK speed/memory:", oak_speed_memory_demo())


if __name__ == "__main__":
    main()
