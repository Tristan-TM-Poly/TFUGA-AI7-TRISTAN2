"""Command-line interface for Ω-VLA-T∞² R0.2-MAX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .address import FrontierCodec
from .catalogs import CATALOG
from .frontier import CampaignConfig, run_campaign
from .oak_max import audit_max_system
from .residual_intelligence import analyze_residual
from .spectral_dna import spectral_dna
from .theorem_factory import TheoremFactory


def _write_or_print(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output is None:
        print(text, end="")
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _parse_json_array(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-r02")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="show the logical frontier")
    manifest.add_argument("--output")

    decode = subparsers.add_parser("decode", help="decode one logical index")
    decode.add_argument("index", type=int)
    decode.add_argument("--output")

    sample = subparsers.add_parser("sample", help="generate finite problem cells")
    sample.add_argument("--count", type=int, default=16)
    sample.add_argument("--seed", type=int, default=0)
    sample.add_argument("--output")

    campaign = subparsers.add_parser(
        "campaign", help="run a finite checkpointable frontier campaign"
    )
    campaign.add_argument("--work-items", type=int, required=True)
    campaign.add_argument("--seed", type=int, default=0)
    campaign.add_argument("--initial-batch", type=int, default=256)
    campaign.add_argument("--min-batch", type=int, default=32)
    campaign.add_argument("--max-batch", type=int, default=8192)
    campaign.add_argument("--records-per-shard", type=int, default=1024)
    campaign.add_argument("--min-utility", type=float, default=0.0)
    campaign.add_argument("--max-risk", type=float, default=1.0)
    campaign.add_argument("--output-dir")
    campaign.add_argument("--report")

    benchmark = subparsers.add_parser("benchmark", help="run deterministic OAK")
    benchmark.add_argument("--seed", type=int, default=17)
    benchmark.add_argument("--campaign-items", type=int, default=257)
    benchmark.add_argument("--output")

    spectral = subparsers.add_parser("spectral-dna")
    spectral.add_argument("matrix", type=_parse_json_array)
    spectral.add_argument("--pseudospectral-points", type=int, default=8)
    spectral.add_argument("--output")

    residual = subparsers.add_parser("residual")
    residual.add_argument("values", type=_parse_json_array)
    residual.add_argument("--output")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "manifest":
        _write_or_print(
            {
                "system": "Ω-VLA-T∞²",
                "version": "R0.2-MAX",
                **CATALOG.summary(),
                "claim_boundary": (
                    "logical addresses and generated candidates are not proofs"
                ),
            },
            args.output,
        )
        return 0

    codec = FrontierCodec()

    if args.command == "decode":
        address = codec.decode(args.index)
        _write_or_print(
            {
                "index": args.index,
                "canonical": address.canonical(),
                "digest": address.digest(),
                "layer": address.layer,
                "program": address.program,
                "coordinates": address.as_mapping(),
            },
            args.output,
        )
        return 0

    if args.command == "sample":
        factory = TheoremFactory()
        cells = [
            factory.generate(address).to_dict()
            for address in codec.iter_sample(args.count, seed=args.seed)
        ]
        _write_or_print(
            {
                "system": "Ω-VLA-T∞²",
                "version": "R0.2-MAX",
                "count": len(cells),
                "cells": cells,
                "theorem_claimed": False,
            },
            args.output,
        )
        return 0

    if args.command == "campaign":
        config = CampaignConfig(
            work_items=args.work_items,
            seed=args.seed,
            initial_batch=args.initial_batch,
            min_batch=args.min_batch,
            max_batch=args.max_batch,
            records_per_shard=args.records_per_shard,
            min_utility=args.min_utility,
            max_risk=args.max_risk,
            output_dir=args.output_dir,
        )
        report = run_campaign(config)
        _write_or_print(report.to_dict(), args.report)
        return 0

    if args.command == "benchmark":
        report = audit_max_system(
            seed=args.seed,
            campaign_items=args.campaign_items,
        )
        _write_or_print(report.to_dict(), args.output)
        return 0 if report.passed else 1

    if args.command == "spectral-dna":
        result = spectral_dna(
            np.asarray(args.matrix),
            pseudospectral_points=args.pseudospectral_points,
        )
        _write_or_print(result.to_dict(), args.output)
        return 0

    if args.command == "residual":
        result = analyze_residual(np.asarray(args.values))
        _write_or_print(result.to_dict(), args.output)
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
