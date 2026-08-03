from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .compiler import IntentCompiler, load_intent
from .models import canonical_json
from .planner import LogicalFrontier


def _emit(payload: Any, output: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-intent",
        description="Compile Tristan intentions into documents, hypergraphs, generators, work units, OAK reports and GitHub dry-run plans.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compile_parser = commands.add_parser("compile", help="Compile a text or JSON intention into an executable evidence bundle.")
    compile_parser.add_argument("intent", help="Intent text or path to a .txt/.md/.json file.")
    compile_parser.add_argument("--output-dir", default="generated/omega_intent_t")
    compile_parser.add_argument("--language", action="append", dest="languages")
    compile_parser.add_argument("--mode", choices=("focused", "expansive", "frontier"), default="expansive")
    compile_parser.add_argument("--materialize-scaffolds", action="store_true")
    compile_parser.add_argument("--github-plan", action="store_true")
    compile_parser.add_argument("--branch", default="feat/omega-intent-generated")

    frontier = commands.add_parser("frontier", help="Inspect or decode the unbounded logical work frontier.")
    frontier.add_argument("--index", type=int)
    frontier.add_argument("--output")

    campaign = commands.add_parser("campaign", help="Stream a finite slice of the logical frontier as addition records.")
    campaign.add_argument("--offset", type=int, default=0)
    campaign.add_argument("--count", type=int, default=100_000)
    campaign.add_argument("--output", default="generated/omega_intent_campaign.jsonl")

    oak = commands.add_parser("oak", help="Read the OAK report from a compiled bundle.")
    oak.add_argument("bundle")
    oak.add_argument("--output")
    return parser


def _campaign(offset: int, count: int, output: str) -> dict[str, Any]:
    frontier = LogicalFrontier()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for index, address in frontier.iter_range(offset, count):
            record = {
                "addition_id": f"FRONTIER-{index:020d}",
                "namespace": f"omega-intent/frontier/{address.domain}",
                "kind": "logical_work_candidate",
                "payload": {"logical_index": index, "address": address.to_dict()},
                "provenance": ["frontier:omega-intent-logical-frontier/v1"],
                "risk": "normal",
                "metadata": {"executed": False, "validated": False},
            }
            handle.write(canonical_json(record) + "\n")
            generated += 1
    return {
        "status": "generated",
        "output": str(path),
        "offset": offset,
        "requested": count,
        "generated": generated,
        "frontier_size": frontier.size,
        "permanent_total_cap": None,
        "executed_work_units": 0,
        "claim_boundary": "logical candidates are not completed or validated work",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "compile":
        intent = load_intent(args.intent, languages=args.languages or ("python",), mode=args.mode)
        result = IntentCompiler().compile(
            intent,
            args.output_dir,
            materialize_scaffolds=args.materialize_scaffolds,
            github_plan=args.github_plan,
            proposed_branch=args.branch,
        )
        _emit(result.to_dict())
        return 0 if result.oak_report.passed else 2
    if args.command == "frontier":
        frontier = LogicalFrontier()
        payload = frontier.manifest()
        if args.index is not None:
            address = frontier.decode(args.index)
            payload = {
                **payload,
                "logical_index": args.index,
                "address": address.to_dict(),
                "roundtrip_index": frontier.encode(address),
            }
        _emit(payload, args.output)
        return 0
    if args.command == "campaign":
        _emit(_campaign(args.offset, args.count, args.output))
        return 0
    if args.command == "oak":
        report_path = Path(args.bundle) / "reports" / "oak.json"
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        _emit(payload, args.output)
        return 0 if payload.get("passed") else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
