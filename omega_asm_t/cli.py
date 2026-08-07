from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze, cvcd_signature
from .backends import emit_dot_u64, supported_variants
from .ir import dot_u64_block_program, load_program
from .oak import oak_report
from .search import estimate_builtin_candidates, pairwise_tradeoffs, pareto_front


def _json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-asm",
        description="Ω-ASM-T∞ R1: OAK-safe assembly analysis and built-in kernel generation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="analyze the built-in unrolled dot-product IR")
    demo.add_argument("--width", type=int, default=4)

    analyze_parser = sub.add_parser("analyze", help="analyze a JSON ASM-IR file")
    analyze_parser.add_argument("path")

    emit = sub.add_parser("emit", help="emit a trusted built-in dot_u64 assembly kernel")
    emit.add_argument("--arch", default="x86_64")
    emit.add_argument("--variant", default="ptr")
    emit.add_argument("--output")

    tournament = sub.add_parser("tournament", help="rank built-in variants conservatively")
    tournament.add_argument("--arch", default="x86_64")

    report = sub.add_parser("report", help="produce a deterministic OAK report")
    report.add_argument("--width", type=int, default=4)
    report.add_argument("--native-verified", action="store_true")
    report.add_argument("--output")

    sub.add_parser("capabilities", help="show supported architectures and variants")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        program = dot_u64_block_program(args.width)
        print(
            _json(
                {
                    "program": program.to_dict(),
                    "metrics": analyze(program).to_dict(),
                    "cvcd": cvcd_signature(program),
                }
            )
        )
        return 0

    if args.command == "analyze":
        program = load_program(args.path)
        print(_json({"metrics": analyze(program).to_dict(), "cvcd": cvcd_signature(program)}))
        return 0

    if args.command == "emit":
        assembly = emit_dot_u64(args.arch, args.variant)
        if args.output:
            Path(args.output).write_text(assembly, encoding="utf-8")
        else:
            print(assembly, end="")
        return 0

    if args.command == "tournament":
        candidates = estimate_builtin_candidates(args.arch)
        print(
            _json(
                {
                    "architecture": args.arch,
                    "warning": "static heuristic only; benchmark on the target CPU before performance claims",
                    "candidates": [candidate.to_dict() for candidate in candidates],
                    "pareto_front": [candidate.to_dict() for candidate in pareto_front(candidates)],
                    "tradeoffs": pairwise_tradeoffs(candidates),
                }
            )
        )
        return 0

    if args.command == "report":
        payload = oak_report(
            dot_u64_block_program(args.width), native_verified=args.native_verified
        ).to_dict()
        text = _json(payload) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    if args.command == "capabilities":
        print(
            _json(
                {
                    "x86_64": list(supported_variants("x86_64")),
                    "aarch64": list(supported_variants("aarch64")),
                }
            )
        )
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
