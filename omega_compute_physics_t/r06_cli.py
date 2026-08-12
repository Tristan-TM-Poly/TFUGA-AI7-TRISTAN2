"""Static R0.6 CLI for fleet intelligence. No target repository code is executed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .call_graph import build_call_graph
from .complexity_ir import compile_source_ir
from .risk_preflight import scan_source_risk
from .snapshot_ledger import snapshot_checkout
from .universal_fleet import scan_universal_fleet


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _mapping(values: list[str], *, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} must use NAME=VALUE syntax: {value!r}")
        name, item = value.split("=", 1)
        if not name or not item:
            raise ValueError(f"invalid {label}: {value!r}")
        result[name] = item
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-compute-r06")
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="hash a checkout into a commit-addressed static snapshot")
    snapshot.add_argument("root")
    snapshot.add_argument("--repository", required=True)
    snapshot.add_argument("--commit", required=True)
    snapshot.add_argument("--output")

    risk = sub.add_parser("risk", help="run conservative static risk preflight on one Python source")
    risk.add_argument("source")
    risk.add_argument("--output")

    graph = sub.add_parser("call-graph", help="compile Python source into static Complexity-IR call graph")
    graph.add_argument("source", nargs="+")
    graph.add_argument("--output")

    fleet = sub.add_parser("universal-fleet", help="scan multiple pinned local checkouts without executing them")
    fleet.add_argument("--repo", action="append", default=[], metavar="NAME=PATH", required=True)
    fleet.add_argument("--commit", action="append", default=[], metavar="NAME=SHA", required=True)
    fleet.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "snapshot":
        report = snapshot_checkout(args.root, repository=args.repository, commit_sha=args.commit)
        _write(report.to_dict(), args.output)
        return 0
    if args.command == "risk":
        path = Path(args.source)
        report = scan_source_risk(path.read_text(encoding="utf-8"), module=str(path))
        _write(report.to_dict(), args.output)
        return 0
    if args.command == "call-graph":
        functions = []
        for item in args.source:
            path = Path(item)
            functions.extend(compile_source_ir(path.read_text(encoding="utf-8"), module=str(path)))
        _write(build_call_graph(functions).to_dict(), args.output)
        return 0
    if args.command == "universal-fleet":
        repos = _mapping(args.repo, label="--repo")
        commits = _mapping(args.commit, label="--commit")
        if set(repos) != set(commits):
            raise ValueError("--repo and --commit must name the same repository keys")
        report = scan_universal_fleet({name: (repos[name], commits[name]) for name in sorted(repos)})
        _write(report.to_dict(), args.output)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
