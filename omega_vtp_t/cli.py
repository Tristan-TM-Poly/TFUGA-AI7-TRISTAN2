"""Command-line interface for Ω-VTP-T++.

Usage examples:
    python -m omega_vtp_t.cli exactness
    python -m omega_vtp_t.cli dynamic --degree 4
    python -m omega_vtp_t.cli benchmark --samples 1024 --dim 8 --degree 3
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from .oakbench_vtp import oak_dynamic_lift_demo, oak_polynomial_exactness_demo
from .tensor_prod_lift import benchmark_lift


def _json_default(value):
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-VTP-T++ TensorProd-Lift CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("exactness", help="Run polynomial exactness OAK demo")

    dynamic = sub.add_parser("dynamic", help="Run lifted dynamic OAK demo")
    dynamic.add_argument("--degree", type=int, default=4)
    dynamic.add_argument("--samples", type=int, default=512)

    bench = sub.add_parser("benchmark", help="Benchmark TensorProd lift speed/memory")
    bench.add_argument("--samples", type=int, default=1024)
    bench.add_argument("--dim", type=int, default=8)
    bench.add_argument("--degree", type=int, default=3)
    bench.add_argument("--basis", choices=["monomial", "one_plus"], default="monomial")
    bench.add_argument("--repeats", type=int, default=3)

    args = parser.parse_args(argv)

    if args.command == "exactness":
        result = oak_polynomial_exactness_demo()
    elif args.command == "dynamic":
        result = oak_dynamic_lift_demo(degree=args.degree, sample_count=args.samples)
    elif args.command == "benchmark":
        rng = np.random.default_rng(2026)
        x = rng.normal(size=(args.samples, args.dim))
        result = benchmark_lift(x, degree=args.degree, basis=args.basis, repeats=args.repeats)
    else:
        raise AssertionError("unreachable")

    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
