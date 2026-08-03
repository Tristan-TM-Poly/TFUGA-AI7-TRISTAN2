"""Command-line interface for the atlas R0.1 seed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import seed_manifest
from .models import EpistemicStatus, OpenStatus, ProblemGenome, ProblemKind
from .oak import evaluate_problem
from .registry import ProblemRegistry


def _load_clay(path: Path) -> ProblemRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for raw in payload["records"]:
        problems.append(
            ProblemGenome(
                problem_id=raw["problem_id"],
                title=raw["title"],
                statement=raw["statement"],
                source_id=payload["source_id"],
                source_locator=raw["source_locator"],
                kind=ProblemKind(raw["kind"]),
                domains=tuple(raw["domains"]),
                objects=tuple(raw.get("objects", ())),
                open_status=OpenStatus(raw["open_status"]),
                epistemic_status=EpistemicStatus(raw["epistemic_status"]),
                last_status_check=payload["last_status_check"],
                literature_search_required=raw["literature_search_required"],
                human_review_required=raw["human_review_required"],
                finite_computation_is_not_proof=raw["finite_computation_is_not_proof"],
                solution_claimed=raw["solution_claimed"],
                metadata=raw.get("metadata", {}),
            )
        )
    return ProblemRegistry(problems)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-open-problems-atlas")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed-1024")
    seed.add_argument("--output", required=True)

    validate = sub.add_parser("validate-clay")
    validate.add_argument(
        "--input", default="data/open_problems_atlas/clay_seed.json"
    )
    validate.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "seed-1024":
        result = seed_manifest()
    else:
        registry = _load_clay(Path(args.input))
        reports = [evaluate_problem(p).to_dict() for p in registry.values()]
        result = {
            "system": "OMEGA-OPEN-PROBLEMS-ATLAS-T-INFINITY",
            "version": "R0.1",
            "registry": registry.summary(),
            "oak_reports": reports,
            "solution_claimed": False,
            "finite_computation_is_not_proof": True,
        }

    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    output = getattr(args, "output", None)
    if output:
        Path(output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
