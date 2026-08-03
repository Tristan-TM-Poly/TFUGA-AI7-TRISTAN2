"""CLI for Ω-VLA-T∞³ R0.3-OMEGA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .compilers import Backend, compile_graphml, default_registry
from .evaluator import evaluate_operator
from .fixtures import finite_operator_fixture, typed_equation_program
from .identities import IdentityFactory, run_identity_trials
from .ir import VLAProgram
from .oak import audit_operator_expression, audit_program
from .operators import operator_expression_from_dict


def _write(text: str, path: str | None) -> None:
    if path is None:
        print(text, end="" if text.endswith("\n") else "\n")
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _write_json(payload: Any, path: str | None) -> None:
    _write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-r03")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="describe the R0.3 wave")
    manifest.add_argument("--output")

    ir_demo = sub.add_parser("ir-demo", help="emit a typed VLA-IR fixture")
    ir_demo.add_argument("--format", choices=("json", "graphml"), default="json")
    ir_demo.add_argument("--output")

    audit_ir = sub.add_parser("audit-ir", help="audit a VLA-IR JSON document")
    audit_ir.add_argument("input")
    audit_ir.add_argument("--output")

    operator_demo = sub.add_parser("operator-demo", help="evaluate and audit a finite operator fixture")
    operator_demo.add_argument("--output")

    compile_command = sub.add_parser("compile", help="compile an OperatorExpr JSON document")
    compile_command.add_argument("input")
    compile_command.add_argument("--backend", choices=tuple(value.value for value in Backend if value != Backend.GRAPHML), required=True)
    compile_command.add_argument("--output")

    identities = sub.add_parser("identity-suite", help="run deterministic numerical identity fixtures")
    identities.add_argument("--trials", type=int, default=32)
    identities.add_argument("--seed", type=int, default=2026)
    identities.add_argument("--output")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "manifest":
        registry = default_registry()
        _write_json(
            {
                "system": "Ω-VLA-T∞³",
                "version": "R0.3-OMEGA-WAVE-1",
                "implemented": [
                    "mathematical type system",
                    "VLA-IR typed graph",
                    "operator expression grammar",
                    "bounded NumPy evaluator",
                    "NumPy/LaTeX/Rust/Lean/JSON/GraphML compilers",
                    "identity and counterexample fixtures",
                    "OAK gates 0-11",
                ],
                "operator_backends": list(registry.backends()),
                "claim_boundaries": {
                    "theorem_claimed": False,
                    "formal_proof_claimed": False,
                    "scientific_validation_claimed": False,
                },
            },
            args.output,
        )
        return 0

    if args.command == "ir-demo":
        program = typed_equation_program()
        if args.format == "json":
            _write(program.canonical_json(indent=2) + "\n", args.output)
        else:
            _write(compile_graphml(program).content, args.output)
        return 0

    if args.command == "audit-ir":
        program = VLAProgram.from_json(Path(args.input).read_text(encoding="utf-8"))
        report = audit_program(program)
        _write_json(report.to_dict(), args.output)
        return 0 if report.passed else 1

    if args.command == "operator-demo":
        expression, environment = finite_operator_fixture()
        result = evaluate_operator(expression, environment)
        report = audit_operator_expression(expression, environment)
        _write_json(
            {
                "expression": expression.to_dict(),
                "simplified": expression.simplify().to_dict(),
                "evaluation": result.to_dict(),
                "oak": report.to_dict(),
            },
            args.output,
        )
        return 0 if report.passed else 1

    if args.command == "compile":
        expression = operator_expression_from_dict(
            json.loads(Path(args.input).read_text(encoding="utf-8"))
        )
        artifact = default_registry().compile(expression, Backend(args.backend))
        _write(artifact.content, args.output)
        return 0 if artifact.complete or args.backend == Backend.LEAN4.value else 2

    if args.command == "identity-suite":
        expression, _ = finite_operator_fixture()
        operator_type = expression.infer_type()
        from .operators import OperatorExpr

        a = OperatorExpr.symbol("A", operator_type)
        b = OperatorExpr.symbol("B", operator_type)
        candidates = [
            IdentityFactory.adjoint_of_composition(a, b),
            IdentityFactory.commutator_antisymmetry(a, b),
            IdentityFactory.commutator_with_identity(a),
            IdentityFactory.tensor_adjoint(a, b),
        ]
        reports = [
            run_identity_trials(
                candidate,
                trials=args.trials,
                seed=args.seed + index,
            ).to_dict()
            for index, candidate in enumerate(candidates)
        ]
        passed = all(report["passed"] for report in reports)
        _write_json(
            {
                "passed": passed,
                "reports": reports,
                "theorem_claimed": False,
                "formal_proof_claimed": False,
            },
            args.output,
        )
        return 0 if passed else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
