"""CLI for the Ω-VLA Wave 2 logical campaign frontier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .campaigns import OperatorCampaignCodec


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output is None:
        print(text, end="")
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-wave2-campaign")
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output")

    decode = commands.add_parser("decode")
    decode.add_argument("index", type=int)
    decode.add_argument("--output")

    plan = commands.add_parser("plan")
    plan.add_argument("--count", type=int, required=True)
    plan.add_argument("--seed", type=int, default=0)
    plan.add_argument("--start-offset", type=int, default=0)
    plan.add_argument("--output")

    audit = commands.add_parser("audit-roundtrip")
    audit.add_argument("--count", type=int, default=1024)
    audit.add_argument("--seed", type=int, default=2026)
    audit.add_argument("--output")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    codec = OperatorCampaignCodec()

    if args.command == "manifest":
        _write(
            {
                **codec.manifest(),
                "codec_digest": codec.deterministic_digest(),
            },
            args.output,
        )
        return 0

    if args.command == "decode":
        address = codec.decode(args.index)
        _write(
            {
                "index": args.index,
                "address": address.to_dict(),
                "canonical": address.canonical(),
                "digest": address.digest(),
                "roundtrip_index": codec.encode(address),
                "theorem_claimed": False,
            },
            args.output,
        )
        return 0

    if args.command == "plan":
        plan = codec.plan(
            args.count,
            seed=args.seed,
            start_offset=args.start_offset,
        )
        _write(plan.to_dict(), args.output)
        return 0

    if args.command == "audit-roundtrip":
        indices = tuple(codec.iter_indices(args.count, seed=args.seed))
        failures = []
        for index in indices:
            address = codec.decode(index)
            encoded = codec.encode(address)
            if encoded != index:
                failures.append(
                    {"index": index, "encoded": encoded, "address": address.to_dict()}
                )
        payload = {
            "count": len(indices),
            "unique_indices": len(set(indices)),
            "failures": failures,
            "passed": not failures and len(indices) == len(set(indices)),
            "logical_frontier_size": codec.size,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }
        _write(payload, args.output)
        return 0 if payload["passed"] else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
