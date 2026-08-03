"""Command-line interface for Ω-POLYGLOT-BENCH-T."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .benchmark import SUPPORTED_BACKENDS, benchmark_backends
from .native import SUPPORTED_NATIVE_BACKENDS, build_native


def _backend_list(value: str) -> tuple[str, ...]:
    result = tuple(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))
    if not result:
        raise argparse.ArgumentTypeError("at least one backend is required")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-polyglot",
        description="Build, verify, benchmark, and select Python/C/C++/Rust backends.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="compile native shared libraries")
    build.add_argument(
        "--backends",
        type=_backend_list,
        default=SUPPORTED_NATIVE_BACKENDS,
        help="comma-separated native backends (default: c,cpp,rust)",
    )

    compare = subparsers.add_parser("compare", help="run conformance and timing benchmarks")
    compare.add_argument(
        "--backends",
        type=_backend_list,
        default=SUPPORTED_BACKENDS,
        help="comma-separated backends (default: python,c,cpp,rust)",
    )
    compare.add_argument("--build-native", action="store_true")
    compare.add_argument("--size", type=int, default=100_000)
    compare.add_argument("--scalar", type=float, default=1.75)
    compare.add_argument("--seed", type=int, default=1729)
    compare.add_argument("--warmups", type=int, default=3)
    compare.add_argument("--repetitions", type=int, default=15)
    compare.add_argument("--tolerance", type=float, default=1e-12)
    compare.add_argument("--output", type=Path)
    return parser


def _write_json(payload: object, output: Path | None = None) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if output is None:
        print(encoded)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded + "\n", encoding="utf-8")
    print(output)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "build":
            built = build_native(arguments.backends)
            _write_json({name: str(path) for name, path in sorted(built.items())})
            return 0

        if arguments.command == "compare":
            if arguments.build_native:
                requested_native = tuple(
                    name for name in arguments.backends if name in SUPPORTED_NATIVE_BACKENDS
                )
                if requested_native:
                    build_native(requested_native)
            report = benchmark_backends(
                size=arguments.size,
                scalar=arguments.scalar,
                seed=arguments.seed,
                warmups=arguments.warmups,
                repetitions=arguments.repetitions,
                tolerance=arguments.tolerance,
                backends=arguments.backends,
            )
            _write_json(report.to_dict(), arguments.output)
            return 0 if report.selected_backend is not None else 2
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"omega-polyglot: {error}", file=sys.stderr)
        return 2

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
