"""Command-line interface for Ω-VLA Wave 3 Identity Factory."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Sequence

from .campaign import CampaignConfig, run_campaign
from .catalog import SCHEMAS, catalog_manifest
from .compilers import compile_property_test, compile_smtlib_counterexample
from .factory import instantiate
from .falsify import test_identity
from .frontier import IdentityFrontierCodec
from .models import IdentityAddress
from .oak import audit_wave3


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _address(args: argparse.Namespace) -> IdentityAddress:
    return IdentityAddress(
        schema_id=args.schema,
        dimension=args.dimension,
        scalar_system=args.scalar,
        matrix_family=args.family,
        mutation_policy=args.mutation,
        trial_profile=args.profile,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla-wave3")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--output")

    catalog = sub.add_parser("catalog")
    catalog.add_argument("--tag")
    catalog.add_argument("--output")

    decode = sub.add_parser("decode")
    decode.add_argument("index", type=int)
    decode.add_argument("--output")

    for name in ("test", "smt", "property-test"):
        command = sub.add_parser(name)
        command.add_argument("schema")
        command.add_argument("--dimension", type=int, default=3)
        command.add_argument("--scalar", choices=("real", "complex"), default="real")
        command.add_argument("--family", default="dense")
        command.add_argument("--mutation", default="none")
        command.add_argument("--profile", default="smoke")
        command.add_argument("--seed", type=int, default=2026)
        command.add_argument("--trials", type=int, default=8)
        command.add_argument("--output")

    campaign = sub.add_parser("campaign")
    campaign.add_argument("--count", type=int, required=True)
    campaign.add_argument("--seed", type=int, default=2026)
    campaign.add_argument("--start-offset", type=int, default=0)
    campaign.add_argument("--trials", type=int, default=4)
    campaign.add_argument("--output")

    oak = sub.add_parser("oak")
    oak.add_argument("--seed", type=int, default=2026)
    oak.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest":
        codec = IdentityFrontierCodec()
        _write({
            "catalog": catalog_manifest(),
            "frontier": codec.manifest().to_dict(),
        }, args.output)
        return 0
    if args.command == "catalog":
        rows = [
            schema.to_dict() for schema in SCHEMAS
            if args.tag is None or args.tag in schema.tags
        ]
        _write({"count": len(rows), "schemas": rows}, args.output)
        return 0
    if args.command == "decode":
        address = IdentityFrontierCodec().decode(args.index)
        _write(address.__dict__, args.output)
        return 0
    if args.command in {"test", "smt", "property-test"}:
        schema, instance = instantiate(_address(args))
        if args.command == "test":
            payload = test_identity(schema, instance, seed=args.seed, trials=args.trials).to_dict()
        elif args.command == "smt":
            payload = compile_smtlib_counterexample(schema, instance).to_dict()
        else:
            payload = compile_property_test(schema, instance, trials=args.trials, seed=args.seed).to_dict()
        _write(payload, args.output)
        return 0
    if args.command == "campaign":
        report = run_campaign(CampaignConfig(
            count=args.count,
            seed=args.seed,
            start_offset=args.start_offset,
            trials_per_identity=args.trials,
        ))
        _write(report.to_dict(), args.output)
        return 0 if report.passed else 1
    if args.command == "oak":
        report = audit_wave3(args.seed)
        _write(report.to_dict(), args.output)
        return 0 if report.passed else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
