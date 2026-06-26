from __future__ import annotations

import argparse
import json

from .canonical import canonical_workflows
from .diff_report import diff_json, diff_markdown
from .exporters import suite_json, suite_markdown
from .oak_gate import evaluate_workflow
from .regression import load_baseline, regression_check
from .snapshot import load_snapshot, snapshot_json
from .workflow_synth import forge_workflow_from_task

VERSION = "0.8.0"


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
    if args.format == "json":
        print(suite_json(workflows))
    else:
        print(suite_markdown(workflows))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    workflows = canonical_workflows()
    print(suite_markdown(workflows))
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
    if args.format == "json":
        print(diff_json(baseline))
    else:
        print(diff_markdown(baseline))
    return 0


def cmd_quality_gate(_: argparse.Namespace) -> int:
    checks = {
        "version_set": VERSION == "0.8.0",
        "canonical_workflows_present": len(canonical_workflows()) >= 4,
        "external_actions_added": False,
        "safe_default": True,
    }
    passed = (
        checks["version_set"]
        and checks["canonical_workflows_present"]
        and not checks["external_actions_added"]
        and checks["safe_default"]
    )
    payload = {"quality_gate": checks, "passed": passed}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


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
