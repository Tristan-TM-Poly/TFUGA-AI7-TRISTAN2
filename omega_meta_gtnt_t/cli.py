from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .engine import MetaGTNTEngine
from .models import RepresentationCandidate


def _load_json_argument(value: str) -> Any:
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-meta-gtnt",
        description="Ω-META-GTNT-T∞² operational frontier/representation compiler",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="emit a deterministic OAK-safe demonstration payload")

    diagnose = sub.add_parser("diagnose", help="classify an operational failure frontier")
    diagnose.add_argument(
        "signals",
        help="JSON object or path to JSON; e.g. '{\"missing_data\": true}'",
    )

    rank = sub.add_parser("rank", help="rank representation candidates")
    rank.add_argument(
        "candidates",
        help="JSON array or path. Fields: name,sparsity,dimension_cost,compute_cost,reconstruction_error,verifiability,invariant_retention",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    engine = MetaGTNTEngine()

    if args.command == "demo":
        payload = engine.demo_payload()
    elif args.command == "diagnose":
        diagnosis = engine.diagnose_failure(_load_json_argument(args.signals))
        payload = {
            "frontier": diagnosis.frontier.value,
            "failure": diagnosis.failure.value,
            "confidence": diagnosis.confidence,
            "rationale": list(diagnosis.rationale),
        }
    elif args.command == "rank":
        raw = _load_json_argument(args.candidates)
        candidates = [RepresentationCandidate(**item) for item in raw]
        payload = [
            {"name": candidate.name, "score": score}
            for candidate, score in engine.rank_representations(candidates)
        ]
    else:  # pragma: no cover
        raise AssertionError(args.command)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
