"""CLI for Ω-VLA R0.3 Wave 2 MAX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .benchmarks import logical_benchmark_frontier, run_atlas
from .commutant import commutant_basis, simultaneous_commutant_basis
from .families import default_family_catalog, materialize_reference
from .genome import OperatorGenome, OperatorGenomeRegistry
from .matrix_functions import matrix_exponential, matrix_logarithm, matrix_sign, matrix_square_root
from .oak_wave2 import audit_wave2
from .properties import infer_properties


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output is None:
        print(text, end="")
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_value(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-wave2")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output")

    catalog = commands.add_parser("catalog")
    catalog.add_argument("--realm")
    catalog.add_argument("--semantic-class")
    catalog.add_argument("--application")
    catalog.add_argument("--text")
    catalog.add_argument("--limit", type=int, default=100)
    catalog.add_argument("--output")

    materialize = commands.add_parser("materialize")
    materialize.add_argument("family_id")
    materialize.add_argument("--dimension", type=int, required=True)
    materialize.add_argument("--parameter", type=float, default=1.0)
    materialize.add_argument("--dense", action="store_true")
    materialize.add_argument("--output")

    properties = commands.add_parser("properties")
    properties.add_argument("matrix", type=_json_value)
    properties.add_argument("--tolerance", type=float, default=1e-10)
    properties.add_argument("--output")

    commutant = commands.add_parser("commutant")
    commutant.add_argument("matrix", type=_json_value, nargs="+")
    commutant.add_argument("--tolerance", type=float)
    commutant.add_argument("--max-dimension", type=int, default=32)
    commutant.add_argument("--output")

    matrix_function = commands.add_parser("matrix-function")
    matrix_function.add_argument("function", choices=("exp", "log", "sqrt", "sign"))
    matrix_function.add_argument("matrix", type=_json_value)
    matrix_function.add_argument("--tolerance", type=float, default=1e-11)
    matrix_function.add_argument("--output")

    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--dimensions", default="4,8,16")
    benchmark.add_argument("--seed", type=int, default=2026)
    benchmark.add_argument("--tolerance", type=float, default=1e-9)
    benchmark.add_argument("--measure-timing", action="store_true")
    benchmark.add_argument("--output")

    genome = commands.add_parser("genome-demo")
    genome.add_argument("--database", default=":memory:")
    genome.add_argument("--output")

    oak = commands.add_parser("oak")
    oak.add_argument("--tolerance", type=float, default=1e-9)
    oak.add_argument("--output")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    catalog = default_family_catalog()

    if args.command == "manifest":
        _write(
            {
                "system": "Ω-VLA-T∞³",
                "version": "R0.3-OMEGA-WAVE-2-MAX",
                "catalog": catalog.summary(),
                "catalog_digest": catalog.digest(),
                "benchmark_frontier": logical_benchmark_frontier(),
                "capabilities": [
                    "csr_reference_kernel",
                    "matrix_free_operators",
                    "pade_newton_matrix_functions",
                    "evidence_aware_properties",
                    "commutant_solver",
                    "bounded_rewrite_saturation",
                    "operator_genome_registry",
                    "deterministic_benchmark_atlas",
                ],
                "theorem_claimed": False,
                "formal_proof_claimed": False,
                "scientific_validation_claimed": False,
            },
            args.output,
        )
        return 0

    if args.command == "catalog":
        if args.limit <= 0:
            raise SystemExit("--limit must be positive")
        matches = catalog.search(
            realm=args.realm,
            semantic_class=args.semantic_class,
            application=args.application,
            text=args.text,
        )
        _write(
            {
                "total_matches": len(matches),
                "returned": min(len(matches), args.limit),
                "families": [value.to_dict() for value in matches[: args.limit]],
                "theorem_claimed": False,
            },
            args.output,
        )
        return 0

    if args.command == "materialize":
        operator = materialize_reference(
            args.family_id,
            args.dimension,
            parameter=args.parameter,
        )
        payload = operator.to_dict()
        if args.dense:
            dense = operator.matrix.to_dense()
            payload["dense_real"] = dense.real.tolist()
            payload["dense_imag"] = dense.imag.tolist()
        _write(payload, args.output)
        return 0

    if args.command == "properties":
        evidence = infer_properties(
            np.asarray(args.matrix, dtype=np.complex128),
            tolerance=args.tolerance,
        )
        _write(
            {
                "evidence": [value.to_dict() for value in evidence],
                "theorem_claimed": False,
                "formal_proof_claimed": False,
            },
            args.output,
        )
        return 0

    if args.command == "commutant":
        matrices = tuple(np.asarray(value, dtype=np.complex128) for value in args.matrix)
        report = (
            commutant_basis(
                matrices[0],
                relative_tolerance=args.tolerance,
                max_dimension=args.max_dimension,
            )
            if len(matrices) == 1
            else simultaneous_commutant_basis(
                matrices,
                relative_tolerance=args.tolerance,
                max_dimension=args.max_dimension,
            )
        )
        _write(report.to_dict(), args.output)
        return 0

    if args.command == "matrix-function":
        matrix = np.asarray(args.matrix, dtype=np.complex128)
        functions = {
            "exp": matrix_exponential,
            "log": matrix_logarithm,
            "sqrt": matrix_square_root,
            "sign": matrix_sign,
        }
        report = functions[args.function](matrix, tolerance=args.tolerance)
        _write(report.to_dict(), args.output)
        return 0 if report.passed else 1

    if args.command == "benchmark":
        try:
            dimensions = tuple(int(value) for value in args.dimensions.split(",") if value)
        except ValueError as exc:
            raise SystemExit("--dimensions must be comma-separated integers") from exc
        report = run_atlas(
            dimensions=dimensions,
            seed=args.seed,
            tolerance=args.tolerance,
            measure_timing=args.measure_timing,
        )
        _write(report.to_dict(), args.output)
        return 0 if report.all_passed else 1

    if args.command == "genome-demo":
        operator = materialize_reference(
            "discrete_geometry.graphs_complexes.combinatorial_laplacian",
            8,
        )
        evidence = infer_properties(operator.matrix.to_dense())
        genome = OperatorGenome(
            genome_id="demo.path_laplacian.n8",
            family_id="discrete_geometry.graphs_complexes.combinatorial_laplacian",
            name="Path Laplacian n=8",
            math_type=operator.math_type,
            representation="csr",
            parameters=(("dimension", "8"),),
            assumptions=("path graph", "unit weights"),
            invariants=("row sums zero except boundary convention",),
            algorithms=("CSR matvec",),
            backends=("python_reference",),
            property_evidence=evidence,
            provenance=("omega-vla-wave2 genome-demo",),
            status="tested",
        )
        with OperatorGenomeRegistry(args.database) as registry:
            inserted, digest = registry.add(genome)
            summary = registry.summary()
        _write(
            {
                "inserted": inserted,
                "digest": digest,
                "genome": genome.to_dict(),
                "registry": summary,
            },
            args.output,
        )
        return 0

    if args.command == "oak":
        report = audit_wave2(tolerance=args.tolerance)
        _write(report.to_dict(), args.output)
        return 0 if report.passed else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
