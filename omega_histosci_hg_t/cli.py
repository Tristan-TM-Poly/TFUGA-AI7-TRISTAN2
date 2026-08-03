"""Command-line interface for Ω-HISTOSCI-HG-T∞ R0.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .models import canonical_dict
from .report import build_report
from .seed import build_seed


def _write_text(path: str | None, content: str) -> None:
    if path is None:
        print(content)
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _write_json(path: str | None, payload: object) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def command_audit(args: argparse.Namespace) -> int:
    report = build_report()
    _write_json(args.output, report)
    return 0 if report["graph"]["valid"] and report["registry"]["valid"] else 2


def command_export_graphml(args: argparse.Namespace) -> int:
    graph, _ = build_seed()
    _write_text(args.output, graph.to_graphml())
    return 0


def command_list_branches(args: argparse.Namespace) -> int:
    _, registry = build_seed()
    branches = []
    for branch_id in sorted(registry.branches):
        branch = registry.branches[branch_id]
        if args.parent is not None and args.parent not in branch.parent_branch_ids:
            continue
        branches.append(canonical_dict(branch))
    _write_json(args.output, {"count": len(branches), "branches": branches})
    return 0


def command_lineage(args: argparse.Namespace) -> int:
    _, registry = build_seed()
    if args.branch_id not in registry.branches:
        raise SystemExit(f"unknown branch: {args.branch_id}")
    payload = {
        "branch": canonical_dict(registry.branches[args.branch_id]),
        "ancestors": list(registry.ancestors_of(args.branch_id)),
        "children": [canonical_dict(branch) for branch in registry.children_of(args.branch_id)],
    }
    _write_json(args.output, payload)
    return 0


def command_stats(args: argparse.Namespace) -> int:
    graph, registry = build_seed()
    payload = {
        "nodes": len(graph.nodes),
        "hyperedges": len(graph.edges),
        "branches": len(registry.branches),
        "macro_branches": len(registry.roots()),
        "sources": len(registry.sources),
        "negative_memories": len(registry.negative_memories),
        "permanent_total_cap": None,
    }
    _write_json(args.output, payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-histoscience")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="validate the deterministic R0.1 fixture")
    audit.add_argument("--output")
    audit.set_defaults(handler=command_audit)

    graphml = subparsers.add_parser("export-graphml", help="export incidence-expanded GraphML")
    graphml.add_argument("--output")
    graphml.set_defaults(handler=command_export_graphml)

    branches = subparsers.add_parser("list-branches", help="list branch records")
    branches.add_argument("--parent")
    branches.add_argument("--output")
    branches.set_defaults(handler=command_list_branches)

    lineage = subparsers.add_parser("lineage", help="show branch ancestors and direct children")
    lineage.add_argument("branch_id")
    lineage.add_argument("--output")
    lineage.set_defaults(handler=command_lineage)

    stats = subparsers.add_parser("stats", help="show seed counts")
    stats.add_argument("--output")
    stats.set_defaults(handler=command_stats)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
