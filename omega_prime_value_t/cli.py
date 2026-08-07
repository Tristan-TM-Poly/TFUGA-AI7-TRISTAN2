from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import deterministic_benchmark
from .campaign import PrimeCampaign, SearchPolicy
from .certificate import verify_certificate
from .families import proth_number
from .ntt import build_ntt_profile
from .primality import primality_status
from .proth import prove_proth


def _write(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def command_search(args: argparse.Namespace) -> int:
    policy = SearchPolicy(
        exponent=args.exponent,
        k_min=args.k_min,
        k_max=args.k_max,
        sieve_bound=args.sieve_bound,
        max_results=args.max_results,
        max_value=args.max_value,
        require_ntt_two_adicity=args.require_ntt_two_adicity,
    )
    _write(PrimeCampaign(policy).run().to_dict(), args.output)
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    value = args.value
    payload: dict[str, Any] = {
        "value": str(value),
        "bit_length": value.bit_length(),
        "decimal_digits": len(str(value)),
        "primality_status": primality_status(value),
    }
    if value < 2**64 and payload["primality_status"] != "composite":
        proof = prove_proth(value)
        payload["proth_proof"] = proof.to_dict() if proof else None
        payload["ntt_profile"] = build_ntt_profile(value).to_dict()
    _write(payload, args.output)
    return 0


def command_proth(args: argparse.Namespace) -> int:
    value = proth_number(args.k, args.exponent)
    proof = prove_proth(value)
    payload = {
        "value": str(value),
        "expression": f"{args.k}*2^{args.exponent}+1",
        "primality_status": primality_status(value),
        "proof": proof.to_dict() if proof else None,
    }
    _write(payload, args.output)
    return 0 if proof else 2


def command_verify(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
    ok, errors = verify_certificate(payload)
    _write({"valid": ok, "errors": errors}, args.output)
    return 0 if ok else 1


def command_benchmark(args: argparse.Namespace) -> int:
    _write(deterministic_benchmark(), args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-prime-value",
        description="OAK-safe public Proth/NTT prime discovery and certification",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="run a deterministic Proth/NTT campaign")
    search.add_argument("--exponent", type=int, required=True)
    search.add_argument("--k-min", type=int, default=1)
    search.add_argument("--k-max", type=int, default=999)
    search.add_argument("--sieve-bound", type=int, default=1000)
    search.add_argument("--max-results", type=int, default=10)
    search.add_argument("--max-value", type=int, default=2**64 - 1)
    search.add_argument("--require-ntt-two-adicity", type=int, default=1)
    search.add_argument("--output")
    search.set_defaults(func=command_search)

    inspect = sub.add_parser("inspect", help="inspect a public integer")
    inspect.add_argument("value", type=int)
    inspect.add_argument("--output")
    inspect.set_defaults(func=command_inspect)

    proth = sub.add_parser("prove-proth", help="construct and prove k*2^n+1")
    proth.add_argument("--k", type=int, required=True)
    proth.add_argument("--exponent", type=int, required=True)
    proth.add_argument("--output")
    proth.set_defaults(func=command_proth)

    verify = sub.add_parser("verify", help="verify an OAKPrime JSON certificate")
    verify.add_argument("certificate")
    verify.add_argument("--output")
    verify.set_defaults(func=command_verify)

    benchmark = sub.add_parser("benchmark", help="emit deterministic R0.1 evidence")
    benchmark.add_argument("--output")
    benchmark.set_defaults(func=command_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
