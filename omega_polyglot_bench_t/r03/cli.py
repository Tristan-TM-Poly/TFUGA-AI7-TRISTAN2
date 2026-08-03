"""Command-line interface for Ω-POLYGLOT-BENCH-T R0.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..native import build_native
from .benchmark import benchmark_throughput


def _parse_sizes(value: str) -> tuple[int, ...]:
    try:
        result = tuple(
            int(item.strip())
            for item in value.split(",")
            if item.strip()
        )
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "sizes must be comma-separated integers"
        ) from error
    if not result or any(item < 0 for item in result):
        raise argparse.ArgumentTypeError("sizes must be non-negative")
    return result


def _parse_backends(value: str) -> tuple[str, ...]:
    result = tuple(item.strip() for item in value.split(",") if item.strip())
    if not result:
        raise argparse.ArgumentTypeError("at least one backend is required")
    unknown = sorted(set(result) - {"c", "cpp", "rust"})
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown native backends: {', '.join(unknown)}"
        )
    return tuple(dict.fromkeys(result))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-polyglot-r03")
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="compile native backends")
    build.add_argument(
        "--backends",
        type=_parse_backends,
        default=("c", "cpp", "rust"),
    )

    benchmark = subcommands.add_parser(
        "benchmark",
        help="compare end-to-end, zero-copy, and prepared native modes",
    )
    benchmark.add_argument("--build-native", action="store_true")
    benchmark.add_argument(
        "--backends",
        type=_parse_backends,
        default=("c", "cpp", "rust"),
    )
    benchmark.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=(4_096, 100_000, 1_000_000),
    )
    benchmark.add_argument("--warmups", type=int, default=3)
    benchmark.add_argument("--repetitions", type=int, default=15)
    benchmark.add_argument("--scalar", type=float, default=1.75)
    benchmark.add_argument("--seed", type=int, default=1729)
    benchmark.add_argument("--tolerance", type=float, default=1e-12)
    benchmark.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "build":
        built = build_native(arguments.backends)
        print(
            json.dumps(
                {backend: str(path) for backend, path in built.items()},
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.build_native:
        build_native(arguments.backends)

    report = benchmark_throughput(
        sizes=arguments.sizes,
        backends=arguments.backends,
        scalar=arguments.scalar,
        seed=arguments.seed,
        warmups=arguments.warmups,
        repetitions=arguments.repetitions,
        tolerance=arguments.tolerance,
    )
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True)
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0
