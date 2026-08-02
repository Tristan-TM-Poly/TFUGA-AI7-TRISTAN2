"""CLI for Ω-GENERATOR-DISCOVERY-STACK."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .autolab import ExperimentCandidate, prioritize_experiments
from .core import compile_morph_ir, identify_affine_1d
from .epistemic import evidence_growth_transition
from .protocol import compile_protocol
from .spectral import compare_spectra


def _json(raw: str):
    path = Path(raw)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(raw)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-generator-discovery",
        description="OAK-safe multi-front generator discovery stack.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    affine = sub.add_parser("affine")
    affine.add_argument("--source", required=True)
    affine.add_argument("--target", required=True)

    spectral = sub.add_parser("spectral")
    spectral.add_argument("--axis", required=True)
    spectral.add_argument("--before", required=True)
    spectral.add_argument("--after", required=True)

    morph = sub.add_parser("compile")
    morph.add_argument("specification")

    epistemic = sub.add_parser("epistemic")
    epistemic.add_argument("--concepts-before", type=float, required=True)
    epistemic.add_argument("--concepts-after", type=float, required=True)
    epistemic.add_argument("--evidence-before", type=float, required=True)
    epistemic.add_argument("--evidence-after", type=float, required=True)

    protocol = sub.add_parser("protocol")
    protocol.add_argument("specification")

    prioritize = sub.add_parser("prioritize")
    prioritize.add_argument("candidates")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "affine":
        result = identify_affine_1d(_json(args.source), _json(args.target)).to_dict()
    elif args.command == "spectral":
        result = compare_spectra(_json(args.axis), _json(args.before), _json(args.after)).to_dict()
    elif args.command == "compile":
        result = compile_morph_ir(_json(args.specification)).to_dict()
    elif args.command == "epistemic":
        result = evidence_growth_transition(
            concepts_before=args.concepts_before,
            concepts_after=args.concepts_after,
            evidence_before=args.evidence_before,
            evidence_after=args.evidence_after,
        ).to_dict()
    elif args.command == "protocol":
        result = compile_protocol(_json(args.specification)).to_dict()
    else:
        raw = _json(args.candidates)
        candidates = [ExperimentCandidate(**item) for item in raw]
        result = [decision.to_dict() for decision in prioritize_experiments(candidates)]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
