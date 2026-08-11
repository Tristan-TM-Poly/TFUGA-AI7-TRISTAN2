from __future__ import annotations

import argparse
import json
from pathlib import Path

from .arena import ArenaCandidate, arena_report
from .budget import AdaptiveBudget
from .ecology import capability_gap_report, ecology_audit
from .synthesis import crossover_specs, fission_spec, synthesize_crossovers


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="omega-skillgen-ultra",
        description="Ω-SKILLGEN Pareto arena, ecology, fusion/fission and adaptive population tools",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    arena = sub.add_parser("arena")
    arena.add_argument("candidates")
    arena.add_argument("--slots", type=int)

    ecology = sub.add_parser("ecology")
    ecology.add_argument("specs", nargs="+")
    ecology.add_argument("--duplicate-threshold", type=float, default=0.82)

    gaps = sub.add_parser("gaps")
    gaps.add_argument("capabilities")
    gaps.add_argument("specs", nargs="+")

    crossover = sub.add_parser("crossover")
    crossover.add_argument("a")
    crossover.add_argument("b")
    crossover.add_argument("name")
    crossover.add_argument("description")
    crossover.add_argument("out")

    fission = sub.add_parser("fission")
    fission.add_argument("spec")
    fission.add_argument("split_index", type=int)
    fission.add_argument("out_dir")

    population = sub.add_parser("population")
    population.add_argument("specs", nargs="+")
    population.add_argument("out_dir")
    population.add_argument("--max-json-chars", type=int, default=5_000_000)
    population.add_argument("--max-candidates", type=int)
    population.add_argument("--min-novelty", type=float, default=0.05)

    args = parser.parse_args()

    if args.cmd == "arena":
        payload = load(args.candidates)
        candidates = [
            ArenaCandidate(
                str(item["name"]),
                dict(item.get("metrics", {})),
                dict(item.get("gates", {})),
                item.get("provenance"),
            )
            for item in payload.get("candidates", [])
        ]
        emit(arena_report(candidates, args.slots))
        return 0

    if args.cmd == "ecology":
        emit(ecology_audit([load(path) for path in args.specs], args.duplicate_threshold))
        return 0

    if args.cmd == "gaps":
        capabilities = load(args.capabilities)
        if isinstance(capabilities, dict):
            capabilities = capabilities.get("capabilities", [])
        emit(capability_gap_report([load(path) for path in args.specs], capabilities))
        return 0

    if args.cmd == "crossover":
        result = crossover_specs(load(args.a), load(args.b), args.name, args.description)
        Path(args.out).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        emit({"status": "WROTE_CANDIDATE", "out": args.out, "lineage": result["lineage"]})
        return 0

    if args.cmd == "fission":
        left, right = fission_spec(load(args.spec), args.split_index)
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for child in (left, right):
            path = out / f"{child['name']}.json"
            path.write_text(json.dumps(child, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            paths.append(str(path))
        emit({"status": "WROTE_CHILDREN", "paths": paths})
        return 0

    if args.cmd == "population":
        specs = [load(path) for path in args.specs]
        budget = AdaptiveBudget(
            max_total_json_chars=args.max_json_chars,
            max_candidates=args.max_candidates,
            min_novelty=args.min_novelty,
        )
        report = synthesize_crossovers(specs, budget)
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for child in report["accepted"]:
            path = out / f"{child['name']}.json"
            path.write_text(json.dumps(child, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            paths.append(str(path))
        serializable = dict(report)
        serializable["accepted"] = [child["name"] for child in report["accepted"]]
        serializable["files"] = paths
        emit(serializable)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
