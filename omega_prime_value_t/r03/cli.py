from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import build_benchmark
from .pocklington import compile_pocklington_certificate, verify_pocklington_certificate


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _factorization(values: list[str]) -> dict[int, int]:
    result: dict[int, int] = {}
    for item in values:
        prime_text, separator, exponent_text = item.partition("^")
        prime = int(prime_text)
        exponent = int(exponent_text) if separator else 1
        result[prime] = result.get(prime, 0) + exponent
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-prime-value-r03")
    subparsers = parser.add_subparsers(dest="command", required=True)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--cpp-kernel")
    benchmark.add_argument("--rust-kernel")
    benchmark.add_argument("--output")

    prove = subparsers.add_parser("prove-pocklington")
    prove.add_argument("n", type=int)
    prove.add_argument("--factor", action="append", required=True, help="known prime power q or q^e")
    prove.add_argument("--max-witness", type=int, default=10_000)
    prove.add_argument("--output")

    verify = subparsers.add_parser("verify-pocklington")
    verify.add_argument("certificate")
    verify.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        _write(build_benchmark(cpp_kernel=args.cpp_kernel, rust_kernel=args.rust_kernel), args.output)
        return 0
    if args.command == "prove-pocklington":
        certificate = compile_pocklington_certificate(
            args.n,
            _factorization(args.factor),
            max_witness=args.max_witness,
        )
        _write(certificate.to_dict(), args.output)
        return 0
    payload = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
    valid, errors = verify_pocklington_certificate(payload)
    _write({"valid": valid, "errors": errors}, args.output)
    return 0 if valid else 1
