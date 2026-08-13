"""Dependency-free CLI for Ω-UVTC-T R0.1 ABI + R0.2 contract layers."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from .compiler import CompileRequest, compile_intent
from .pipeline import run_pipeline
from .portfolio import GoCandidate, select_go_move


def _dump(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Omega UVTC Universal Verified Transformation Compiler")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_p = sub.add_parser("compile")
    compile_p.add_argument("--intent", required=True)
    compile_p.add_argument("--goal", required=True)
    compile_p.add_argument("--formal", action="store_true")

    pipeline_p = sub.add_parser("pipeline")
    pipeline_p.add_argument("--intent", required=True)
    pipeline_p.add_argument("--goal", required=True)
    pipeline_p.add_argument("--formal", action="store_true")

    sub.add_parser("portfolio-demo")
    args = parser.parse_args(argv)

    if args.command == "compile":
        program = compile_intent(CompileRequest(args.intent, args.goal, formal=args.formal))
        _dump({
            "schema_version": program.schema_version,
            "program_id": program.program_id,
            "fingerprint": program.fingerprint,
            "instructions": [
                {"primitive": i.primitive.value, "kernel": i.kernel.value, "args": dict(i.args)}
                for i in program.instructions
            ],
        })
        return 0
    if args.command == "pipeline":
        _dump(asdict(run_pipeline(CompileRequest(args.intent, args.goal, formal=args.formal))))
        return 0
    if args.command == "portfolio-demo":
        candidates = (
            GoCandidate("reuse", 2, 2, 2, 3, 3, 1, 1, 0, 1, 1, 1),
            GoCandidate("duplicate", 1, 1, 1, 1, 1, 2, 2, 3, 2, 2, 2),
            GoCandidate("explore", 3, 3, 1, 1, 3, 3, 1, 0, 2, 3, 2),
        )
        _dump(asdict(select_go_move(candidates, minimum_density=0.1)))
        return 0
    return 2
