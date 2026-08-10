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
from .replication import aggregate_p5_reports
from .search import estimate_builtin_candidates, pairwise_tradeoffs, pareto_front


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

    benchmark_report = sub.add_parser(
        "benchmark-report",
        help="summarize observational native timing JSON with robust statistics",
    )
    benchmark_report.add_argument("path")
    benchmark_report.add_argument("--output")

    microarch = sub.add_parser(
        "microarch", help="emit an observational microarchitecture/cache/ISA manifest"
    )
    microarch.add_argument("--toolchains", action="store_true")
    microarch.add_argument("--output")

    p5 = sub.add_parser(
        "p5-report",
        help="parse externally collected perf-stat evidence into a provenance-rich P5 report",
    )
    p5.add_argument("path", help="perf stat stderr captured with -x ';' --no-big-num")
    p5.add_argument("--binary", help="optional measured binary path for SHA-256 provenance")
    p5.add_argument("--exit-code", type=int)
    p5.add_argument("--output")

    p6 = sub.add_parser(
        "p6-aggregate",
        help="aggregate P5 reports into conservative identified-target replication groups",
    )
    p6.add_argument("paths", nargs="+", help="P5 report JSON files")
    p6.add_argument("--min-replicates", type=int, default=3)
    p6.add_argument("--output")

    p7_obligation = sub.add_parser(
        "p7-obligation",
        help="compile a fixed-width bit-vector equivalence spec into a replayable SMT-LIB obligation",
    )
    p7_obligation.add_argument("path", help="equivalence specification JSON")
    p7_obligation.add_argument("--output")

    p7_certificate = sub.add_parser(
        "p7-certificate",
        help="build a bounded equivalence certificate from exhaustive checking plus optional external solver text",
    )
    p7_certificate.add_argument("path", help="equivalence specification JSON")
    p7_certificate.add_argument("--solver-result", help="optional externally produced sat/unsat/unknown text")
    p7_certificate.add_argument("--solver-name")
    p7_certificate.add_argument("--solver-version")
    p7_certificate.add_argument("--max-states", type=int, default=1_000_000)
    p7_certificate.add_argument("--output")

    sub.add_parser("p5-events", help="show the conservative perf event request set")
    sub.add_parser("machine", help="emit the R1 conservative execution-context manifest")
    sub.add_parser("capabilities", help="show supported architectures, variants and evidence surfaces")
    return parser


def _benchmark_report(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    sample_groups = payload.get("samples_ns_per_call")
    if not isinstance(sample_groups, dict) or not sample_groups:
        raise ValueError("benchmark JSON must contain non-empty samples_ns_per_call")

    summaries = {}
    summary_objects = {}
    for name, samples in sample_groups.items():
        if not isinstance(name, str) or not isinstance(samples, list):
            raise ValueError("benchmark sample groups must map names to lists")
        summary = summarize_samples(samples)
        summary_objects[name] = summary
        summaries[name] = summary.to_dict()

    reference = summary_objects.get("reference_c")
    ratios: dict[str, float | None] = {}
    if reference is not None:
        for name, summary in summary_objects.items():
            ratios[name] = relative_ratio(summary, reference)

    metadata = {key: value for key, value in payload.items() if key != "samples_ns_per_call"}
    return {
        "evidence_level": "P4-observational",
        "claim_scope": "single_execution_context_only",
        "warning": (
            "timings are observational; do not generalize speedups without controlled target-CPU replication"
        ),
        "machine": machine_manifest(),
        "native_metadata": metadata,
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
        _write_or_print(payload, args.output)
        return 0

    if args.command == "benchmark-report":
        _write_or_print(_benchmark_report(args.path), args.output)
        return 0

    if args.command == "microarch":
        _write_or_print(
            microarchitecture_manifest(include_toolchains=args.toolchains), args.output
        )
        return 0

    if args.command == "p5-report":
        perf_text = Path(args.path).read_text(encoding="utf-8", errors="replace")
        _write_or_print(
            build_p5_report(
                perf_text,
                source_exit_code=args.exit_code,
                binary_path=args.binary,
            ),
            args.output,
        )
        return 0

    if args.command == "p6-aggregate":
        reports = [_load_json_object(path) for path in args.paths]
        _write_or_print(
            aggregate_p5_reports(reports, min_replicates=args.min_replicates), args.output
        )
        return 0

    if args.command == "p7-obligation":
        _write_or_print(build_equivalence_obligation(_load_json_object(args.path)), args.output)
        return 0

    if args.command == "p7-certificate":
        solver_text = (
            Path(args.solver_result).read_text(encoding="utf-8", errors="replace")
            if args.solver_result
            else None
        )
        _write_or_print(
            build_p7_certificate(
                _load_json_object(args.path),
                solver_text=solver_text,
                solver_name=args.solver_name,
                solver_version=args.solver_version,
                max_states=args.max_states,
            ),
            args.output,
        )
        return 0

    if args.command == "p5-events":
        print(_json({"events": list(requested_perf_events())}))
        return 0

    if args.command == "machine":
        print(_json(machine_manifest()))
        return 0

    if args.command == "capabilities":
        print(
            _json(
                {
                    "x86_64": list(supported_variants("x86_64")),
                    "aarch64": list(supported_variants("aarch64")),
                    "evidence": {
                        "P1": "static structure",
                        "P2": "versioned uncalibrated heuristic",
                        "P3": "native differential correctness",
                        "P4": "observational timing",
                        "P5": "externally collected hardware-counter parsing and provenance",
                        "P6": "identified-target replication grouping; no universal promotion",
                        "P7": "bounded fixed-width bit-vector obligation/certificate; kernel_checked=false",
                    },
                    "p5_perf_events": list(requested_perf_events()),
                    "arbitrary_command_execution": False,
                    "package_executes_solver": False,
                }
            )
        )
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
