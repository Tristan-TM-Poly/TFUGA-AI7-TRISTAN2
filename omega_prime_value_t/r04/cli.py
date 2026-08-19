from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .benchmark import deterministic_benchmark
from .budget import BudgetLedger, ComputeBudgetPolicy, ComputeObservation
from .external import import_external_artifact, verify_with_external_command
from .proof_dag import build_proof_graph, verify_proof_graph
from .residue import compile_proth_residue_program, filter_receipt, verify_residue_program
from .transparency import TransparencyLog, verify_checkpoint


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-prime-value-r04")
    sub = parser.add_subparsers(dest="command", required=True)

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--output")

    graph = sub.add_parser("build-proof-graph")
    graph.add_argument("certificate")
    graph.add_argument("--output")

    verify_graph = sub.add_parser("verify-proof-graph")
    verify_graph.add_argument("graph")
    verify_graph.add_argument("--output")

    residues = sub.add_parser("compile-residues")
    residues.add_argument("--exponent-min", type=int, required=True)
    residues.add_argument("--exponent-max", type=int, required=True)
    residues.add_argument("--prime-bound", type=int, default=10_000)
    residues.add_argument("--output")

    scan = sub.add_parser("scan-residues")
    scan.add_argument("program")
    scan.add_argument("--exponent", type=int, required=True)
    scan.add_argument("--k-start", type=int, required=True)
    scan.add_argument("--k-stop", type=int, required=True)
    scan.add_argument("--segment-size", type=int, default=65_536)
    scan.add_argument("--output")

    transparency = sub.add_parser("transparency-append")
    transparency.add_argument("database")
    transparency.add_argument("kind")
    transparency.add_argument("payload")
    transparency.add_argument("--created-at", default="2026-08-03T00:00:00+00:00")
    transparency.add_argument("--output")

    external = sub.add_parser("import-external")
    external.add_argument("artifact")
    external.add_argument("--format", required=True)
    external.add_argument("--source-label", required=True)
    external.add_argument("--verifier")
    external.add_argument("--marker", default="PRIME")
    external.add_argument("--output")

    budget = sub.add_parser("budget-demo")
    budget.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        _write(deterministic_benchmark(), args.output)
        return 0
    if args.command == "build-proof-graph":
        certificate = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        _write(build_proof_graph(certificate).to_dict(), args.output)
        return 0
    if args.command == "verify-proof-graph":
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        valid, errors = verify_proof_graph(graph)
        _write({"valid": valid, "errors": errors}, args.output)
        return 0 if valid else 2
    if args.command == "compile-residues":
        program = compile_proth_residue_program(
            args.exponent_min,
            args.exponent_max,
            prime_bound=args.prime_bound,
        )
        _write(program.to_dict(), args.output)
        return 0
    if args.command == "scan-residues":
        program = json.loads(Path(args.program).read_text(encoding="utf-8"))
        valid, errors = verify_residue_program(program)
        if not valid:
            _write({"valid": False, "errors": errors}, args.output)
            return 2
        _write(
            filter_receipt(
                program,
                args.exponent,
                args.k_start,
                args.k_stop,
                segment_size=args.segment_size,
            ),
            args.output,
        )
        return 0
    if args.command == "transparency-append":
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        with TransparencyLog(args.database) as log:
            entry = log.append(args.kind, payload)
            chain_valid, chain_errors = log.verify_chain()
            checkpoint = log.checkpoint(created_at_utc=args.created_at)
            checkpoint_valid, checkpoint_errors = verify_checkpoint(checkpoint, log.entries())
        _write(
            {
                "entry": entry.to_dict(),
                "chain_valid": chain_valid,
                "chain_errors": chain_errors,
                "checkpoint": checkpoint.to_dict(),
                "checkpoint_valid": checkpoint_valid,
                "checkpoint_errors": checkpoint_errors,
            },
            args.output,
        )
        return 0
    if args.command == "import-external":
        data = Path(args.artifact).read_bytes()
        imported = import_external_artifact(data, format=args.format, source_label=args.source_label)
        payload: dict[str, Any] = {"import": imported.to_dict()}
        if args.verifier:
            payload["verification"] = verify_with_external_command(
                data,
                imported,
                executable=args.verifier,
                arguments=("{artifact}",),
                output_marker=args.marker,
            ).to_dict()
        _write(payload, args.output)
        return 0
    if args.command == "budget-demo":
        ledger = BudgetLedger(ComputeBudgetPolicy(100.0, 10_000, 1.0, 10.0, 0.1, 2))
        ledger.record(ComputeObservation("fixture", "product", 5.0, 100, 0.01, 0.02, 4.0))
        _write(ledger.report(), args.output)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
