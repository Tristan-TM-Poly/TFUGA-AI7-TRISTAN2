from __future__ import annotations

import argparse
import json

from .canonical import canonical_workflows
from .diff_report import diff_json, diff_markdown
from .exporters import suite_json, suite_markdown
from .oak_gate import evaluate_workflow
from .orchestrator import run_orchestrator
from .regression import load_baseline, regression_check
from .release import quality_gate, release_markdown, release_pipeline
from .snapshot import load_snapshot, snapshot_json
from .workflow_synth import forge_workflow_from_task

VERSION = "1.0.0"


def cmd_version(_: argparse.Namespace) -> int:
    print(VERSION)
    return 0


def cmd_forge(args: argparse.Namespace) -> int:
    workflow = forge_workflow_from_task(args.task)
    report = evaluate_workflow(workflow)
    payload = {}
    payload.update(workflow.to_dict())
    payload.update(report.to_dict())
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    workflows = canonical_workflows()
    print(suite_json(workflows) if args.format == "json" else suite_markdown(workflows))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    print(suite_markdown(canonical_workflows()))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    baseline = load_baseline(args.against) if args.against else None
    result = regression_check(baseline)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    print(snapshot_json(VERSION))
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    baseline = load_snapshot(args.against) if args.against else None
    print(diff_json(baseline) if args.format == "json" else diff_markdown(baseline))
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    baseline = load_snapshot(args.against) if args.against else None
    if args.format == "json":
        payload = release_pipeline(VERSION, baseline)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["passed"] else 1
    text = release_markdown(VERSION, baseline)
    print(text)
    return 0 if "Passed: True" in text.splitlines()[3] else 1


def cmd_orchestrate(args: argparse.Namespace) -> int:
    result = run_orchestrator(VERSION, actions=args.actions or [])
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "release_candidate" else 1


def cmd_quality_gate(_: argparse.Namespace) -> int:
    payload = quality_gate(VERSION)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto2", description="Ω-AUTO²-Kernel CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    version = sub.add_parser("version", help="Print AUTO2 version")
    version.set_defaults(func=cmd_version)

    forge = sub.add_parser("forge", help="Forge an OAK-safe workflow draft")
    forge.add_argument("task")
    forge.set_defaults(func=cmd_forge)

    bench = sub.add_parser("bench", help="Run canonical benchmark suite")
    bench.add_argument("target", choices=["canonical"])
    bench.add_argument("--format", choices=["json", "markdown"], default="markdown")
    bench.set_defaults(func=cmd_bench)

    compare = sub.add_parser("compare", help="Compare current canonical suite against a baseline")
    compare.add_argument("target", choices=["canonical"])
    compare.add_argument("--against", default=None)
    compare.set_defaults(func=cmd_compare)

    snapshot = sub.add_parser("snapshot", help="Generate a canonical benchmark snapshot")
    snapshot.add_argument("target", choices=["canonical"])
    snapshot.set_defaults(func=cmd_snapshot)

    diff = sub.add_parser("diff", help="Generate a benchmark diff report")
    diff.add_argument("target", choices=["canonical"])
    diff.add_argument("--against", default=None)
    diff.add_argument("--format", choices=["json", "markdown"], default="markdown")
    diff.set_defaults(func=cmd_diff)

    release_check = sub.add_parser("release-check", help="Run local release pipeline")
    release_check.add_argument("target", choices=["canonical"])
    release_check.add_argument("--against", default=None)
    release_check.add_argument("--format", choices=["json", "markdown"], default="markdown")
    release_check.set_defaults(func=cmd_release_check)

    orchestrate = sub.add_parser("orchestrate", help="Run AUTO2 v1 orchestrator")
    orchestrate.add_argument("target", choices=["canonical"])
    orchestrate.add_argument("--actions", nargs="*", default=[])
    orchestrate.set_defaults(func=cmd_orchestrate)

    report = sub.add_parser("report", help="Generate reports")
    report.add_argument("target", choices=["canonical"])
    report.set_defaults(func=cmd_report)

    quality_gate = sub.add_parser("quality-gate", help="Run lightweight quality gate")
    quality_gate.set_defaults(func=cmd_quality_gate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
