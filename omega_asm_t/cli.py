from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze, cvcd_signature
from .backends import emit_dot_u64, supported_variants
from .benchmark import machine_manifest, relative_ratio, summarize_samples
from .counters import build_p5_report, requested_perf_events
from .formal import build_equivalence_obligation, build_p7_certificate
from .ir import dot_u64_block_program, load_program
from .microarch import microarchitecture_manifest
from .oak import oak_report
from .parallax import build_parallax_report
from .replication import aggregate_p5_reports
from .search import estimate_builtin_candidates, pairwise_tradeoffs, pareto_front
from .superopt import superoptimize


def _json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _write_or_print(payload: object, output: str | None) -> None:
    text = _json(payload) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-asm",
        description="Ω-ASM-T∞: OAK-safe assembly analysis, evidence and trusted kernel laboratory",
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

    benchmark_report = sub.add_parser("benchmark-report", help="summarize observational native timing JSON")
    benchmark_report.add_argument("path")
    benchmark_report.add_argument("--output")

    parallax = sub.add_parser("parallax-report", help="hash externally built compiler-parallax artifacts")
    parallax.add_argument("path")
    parallax.add_argument("--output")

    superopt = sub.add_parser("superopt", help="run bounded proof-first bit-vector rewrite search")
    superopt.add_argument("path", help="superoptimizer JSON specification")
    superopt.add_argument("--max-candidates", type=int, default=128)
    superopt.add_argument("--max-states", type=int, default=1_000_000)
    superopt.add_argument("--output")

    microarch = sub.add_parser("microarch", help="emit observational microarchitecture/cache/ISA manifest")
    microarch.add_argument("--toolchains", action="store_true")
    microarch.add_argument("--output")

    p5 = sub.add_parser("p5-report", help="parse externally collected perf-stat evidence")
    p5.add_argument("path")
    p5.add_argument("--binary")
    p5.add_argument("--exit-code", type=int)
    p5.add_argument("--output")

    p6 = sub.add_parser("p6-aggregate", help="aggregate P5 reports into identified-target replication groups")
    p6.add_argument("paths", nargs="+")
    p6.add_argument("--min-replicates", type=int, default=3)
    p6.add_argument("--output")

    p7_obligation = sub.add_parser("p7-obligation", help="compile a bit-vector equivalence spec into SMT-LIB")
    p7_obligation.add_argument("path")
    p7_obligation.add_argument("--output")

    p7_certificate = sub.add_parser("p7-certificate", help="build a bounded equivalence certificate")
    p7_certificate.add_argument("path")
    p7_certificate.add_argument("--solver-result")
    p7_certificate.add_argument("--solver-name")
    p7_certificate.add_argument("--solver-version")
    p7_certificate.add_argument("--max-states", type=int, default=1_000_000)
    p7_certificate.add_argument("--output")

    sub.add_parser("p5-events", help="show conservative perf event set")
    sub.add_parser("machine", help="emit the R1 execution-context manifest")
    sub.add_parser("capabilities", help="show supported architectures and evidence surfaces")
    return parser


def _benchmark_report(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    groups = payload.get("samples_ns_per_call")
    if not isinstance(groups, dict) or not groups:
        raise ValueError("benchmark JSON must contain non-empty samples_ns_per_call")
    summaries, objects = {}, {}
    for name, samples in groups.items():
        if not isinstance(name, str) or not isinstance(samples, list):
            raise ValueError("benchmark sample groups must map names to lists")
        summary = summarize_samples(samples)
        objects[name] = summary
        summaries[name] = summary.to_dict()
    reference = objects.get("reference_c")
    ratios = {name: relative_ratio(summary, reference) for name, summary in objects.items()} if reference else {}
    return {
        "evidence_level": "P4-observational",
        "claim_scope": "single_execution_context_only",
        "warning": "timings are observational; do not generalize speedups without controlled target-CPU replication",
        "machine": machine_manifest(),
        "native_metadata": {key: value for key, value in payload.items() if key != "samples_ns_per_call"},
        "statistics_ns_per_call": summaries,
        "median_ratio_to_reference_c": ratios,
    }


def _load_json_object(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        program = dot_u64_block_program(args.width)
        print(_json({"program": program.to_dict(), "metrics": analyze(program).to_dict(), "cvcd": cvcd_signature(program)}))
        return 0
    if args.command == "analyze":
        program = load_program(args.path)
        print(_json({"metrics": analyze(program).to_dict(), "cvcd": cvcd_signature(program)}))
        return 0
    if args.command == "emit":
        assembly = emit_dot_u64(args.arch, args.variant)
        if args.output: Path(args.output).write_text(assembly, encoding="utf-8")
        else: print(assembly, end="")
        return 0
    if args.command == "tournament":
        candidates = estimate_builtin_candidates(args.arch)
        print(_json({"architecture": args.arch, "warning": "static heuristic only; benchmark on target CPU before performance claims", "candidates": [c.to_dict() for c in candidates], "pareto_front": [c.to_dict() for c in pareto_front(candidates)], "tradeoffs": pairwise_tradeoffs(candidates)}))
        return 0
    if args.command == "report":
        _write_or_print(oak_report(dot_u64_block_program(args.width), native_verified=args.native_verified).to_dict(), args.output); return 0
    if args.command == "benchmark-report":
        _write_or_print(_benchmark_report(args.path), args.output); return 0
    if args.command == "parallax-report":
        _write_or_print(build_parallax_report(_load_json_object(args.path)), args.output); return 0
    if args.command == "superopt":
        _write_or_print(superoptimize(_load_json_object(args.path), max_candidates=args.max_candidates, max_states=args.max_states), args.output); return 0
    if args.command == "microarch":
        _write_or_print(microarchitecture_manifest(include_toolchains=args.toolchains), args.output); return 0
    if args.command == "p5-report":
        text = Path(args.path).read_text(encoding="utf-8", errors="replace")
        _write_or_print(build_p5_report(text, source_exit_code=args.exit_code, binary_path=args.binary), args.output); return 0
    if args.command == "p6-aggregate":
        _write_or_print(aggregate_p5_reports([_load_json_object(p) for p in args.paths], min_replicates=args.min_replicates), args.output); return 0
    if args.command == "p7-obligation":
        _write_or_print(build_equivalence_obligation(_load_json_object(args.path)), args.output); return 0
    if args.command == "p7-certificate":
        solver_text = Path(args.solver_result).read_text(encoding="utf-8", errors="replace") if args.solver_result else None
        _write_or_print(build_p7_certificate(_load_json_object(args.path), solver_text=solver_text, solver_name=args.solver_name, solver_version=args.solver_version, max_states=args.max_states), args.output); return 0
    if args.command == "p5-events":
        print(_json({"events": list(requested_perf_events())})); return 0
    if args.command == "machine":
        print(_json(machine_manifest())); return 0
    if args.command == "capabilities":
        print(_json({
            "x86_64": list(supported_variants("x86_64")), "aarch64": list(supported_variants("aarch64")),
            "evidence": {
                "P1":"static structure", "P2":"versioned uncalibrated heuristic", "P3":"native differential correctness",
                "P4":"observational timing", "P5":"externally collected hardware counters", "P6":"identified-target replication",
                "P7":"bounded bit-vector certificates; kernel_checked=false",
                "parallax":"separate-translation-unit C/C++/Rust/ASM provenance",
                "superopt":"bounded proof-first rewrite search; structural cost only",
            },
            "p5_perf_events": list(requested_perf_events()),
            "arbitrary_command_execution": False, "package_executes_solver": False, "package_executes_compilers": False,
        })); return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
