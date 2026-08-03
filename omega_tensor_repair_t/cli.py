"""Command-line interface for Ω-TENSOR-REPAIR-T R0.1–R0.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .benchmark import run_benchmark
from .benchmark_r02 import run_benchmark_r02
from .benchmark_r03 import run_benchmark_r03
from .clebsch_gordan import su2_clebsch_gordan
from .compiler import compile_spec
from .irreducible_basis import basis_orthonormality_error, square_irreducible_basis
from .oak import audit_bundle
from .projectors import analyze_2d, dimension_identity
from .young import young_dimension_atlas


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

    basis = subparsers.add_parser("basis", help="emit the arbitrary-dimensional irreducible rank-2 basis")
    basis.add_argument("size", type=int)
    basis.add_argument("--include-matrices", action="store_true")
    basis.add_argument("--output")

    young = subparsers.add_parser("young", help="emit Young partitions and Schur dimensions")
    young.add_argument("order", type=int)
    young.add_argument("ambient_dimension", type=int)
    young.add_argument("--output")

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

    benchmark_r03 = subparsers.add_parser("benchmark-r03", help="run irreducible-basis and Young R0.3 fixtures")
    benchmark_r03.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze-2d":
        bundle = analyze_2d(args.left, args.right)
        payload = {"bundle": bundle.to_dict(), "oak": audit_bundle(bundle).to_dict()}
        return _json_dump(payload, args.output)
    if args.command == "dimensions":
        return _json_dump(dimension_identity(args.size), args.output)
    if args.command == "basis":
        elements = square_irreducible_basis(args.size)
        payload = {
            "size": args.size,
            "cardinality": len(elements),
            "orthonormality_error": basis_orthonormality_error(elements),
            "elements": [
                {
                    "name": element.name,
                    "sector": element.sector,
                    **({"matrix": [list(row) for row in element.matrix]} if args.include_matrices else {}),
                }
                for element in elements
            ],
        }
        return _json_dump(payload, args.output)
    if args.command == "young":
        return _json_dump(
            {
                "order": args.order,
                "ambient_dimension": args.ambient_dimension,
                "atlas": young_dimension_atlas(args.order, args.ambient_dimension),
            },
            args.output,
        )
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
    if args.command == "benchmark-r03":
        return _json_dump(run_benchmark_r03(), args.output)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
