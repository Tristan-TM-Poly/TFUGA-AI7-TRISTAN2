"""Command-line interface for Ω-TENSOR-REPAIR-T R0.1–R0.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .benchmark import run_benchmark
from .benchmark_r02 import run_benchmark_r02
from .clebsch_gordan import su2_clebsch_gordan
from .compiler import compile_spec
from .oak import audit_bundle
from .projectors import analyze_2d, dimension_identity


def _json_dump(payload: Any, output: str | None) -> int:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-tensor-repair")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze-2d", help="compile the exact 4→3+1→2+1+1 bundle")
    analyze.add_argument("--left", nargs=2, type=float, required=True)
    analyze.add_argument("--right", nargs=2, type=float, required=True)
    analyze.add_argument("--output")

    dimensions = subparsers.add_parser("dimensions", help="show the rank-2 square dimension identity")
    dimensions.add_argument("size", type=int)
    dimensions.add_argument("--output")

    su2 = subparsers.add_parser("su2", help="show SU(2) Clebsch-Gordan dimension branching")
    su2.add_argument("left_dimension", type=int)
    su2.add_argument("right_dimension", type=int)
    su2.add_argument("--output")

    compile_command = subparsers.add_parser("compile", help="compile a JSON TensorProdLift-T specification")
    compile_command.add_argument("spec")
    compile_command.add_argument("--output")

    benchmark = subparsers.add_parser("benchmark", help="run deterministic R0.1 finite OAK fixtures")
    benchmark.add_argument("--output")

    benchmark_r02 = subparsers.add_parser("benchmark-r02", help="run higher-order R0.2 fixtures")
    benchmark_r02.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze-2d":
        bundle = analyze_2d(args.left, args.right)
        payload = {"bundle": bundle.to_dict(), "oak": audit_bundle(bundle).to_dict()}
        return _json_dump(payload, args.output)
    if args.command == "dimensions":
        return _json_dump(dimension_identity(args.size), args.output)
    if args.command == "su2":
        return _json_dump(
            su2_clebsch_gordan(args.left_dimension, args.right_dimension).to_dict(),
            args.output,
        )
    if args.command == "compile":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        return _json_dump(compile_spec(spec).to_dict(), args.output)
    if args.command == "benchmark":
        return _json_dump(run_benchmark(), args.output)
    if args.command == "benchmark-r02":
        return _json_dump(run_benchmark_r02(), args.output)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
