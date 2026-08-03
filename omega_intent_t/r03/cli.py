from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .models import ValidationReceipt
from .oak import run_oakbench
from .proof import ProofArtifactBuilder
from .router import ImpactRouter
from .scanner import RepoTwinScanner


def _emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-intent-r03", description="RepoTwin, impact routing and proof-carrying artifacts")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="Build a deterministic repository twin")
    scan.add_argument("root", nargs="?", default=".")
    scan.add_argument("--output")

    route = commands.add_parser("route", help="Route changed paths to packages, tests and workflows")
    route.add_argument("root", nargs="?", default=".")
    route.add_argument("--changed", action="append", default=[])
    route.add_argument("--changed-file", help="Text file containing one changed path per line")
    route.add_argument("--output")

    proof = commands.add_parser("proof", help="Create a proof-carrying artifact envelope")
    proof.add_argument("path")
    proof.add_argument("--root")
    proof.add_argument("--provenance", action="append", required=True)
    proof.add_argument("--derived-from", action="append", default=[])
    proof.add_argument("--risk", action="append", default=[])
    proof.add_argument("--validator", default="manual-review")
    proof.add_argument("--validation-status", default="pending")
    proof.add_argument("--validation-command", default="")
    proof.add_argument("--epistemic-status", default="PROTOTYPED")
    proof.add_argument("--publication-authorized", action="store_true")
    proof.add_argument("--output")

    oak = commands.add_parser("oak", help="Run deterministic R0.3 OAK fixtures")
    oak.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        payload = RepoTwinScanner().scan(args.root).to_dict()
    elif args.command == "route":
        changed = list(args.changed)
        if args.changed_file:
            changed.extend(line.strip() for line in Path(args.changed_file).read_text(encoding="utf-8").splitlines() if line.strip())
        manifest = RepoTwinScanner().scan(args.root)
        payload = ImpactRouter().route(manifest, changed).to_dict()
    elif args.command == "proof":
        receipt = ValidationReceipt(
            validator=args.validator,
            status=args.validation_status,
            command=args.validation_command,
        )
        artifact = ProofArtifactBuilder().build(
            args.path,
            root=args.root,
            provenance=args.provenance,
            derived_from=args.derived_from,
            validations=(receipt,),
            epistemic_status=args.epistemic_status,
            risks=args.risk,
            publication_authorized=args.publication_authorized,
        )
        payload = artifact.to_dict()
    elif args.command == "oak":
        result = run_oakbench()
        payload = result.to_dict()
        _emit(payload, args.output)
        return 0 if result.passed else 2
    else:
        raise AssertionError("unreachable")
    _emit(payload, args.output)
    return 0
