"""CLI for the Tristan multi-repository Python runtime."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .repo_registry import RepoRegistry
from .runtime import PipelineStep, TristanRuntime


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _payload(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("payload JSON must be an object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-tristan-runtime",
        description="Inspect and execute Tristan Python repositories through one plugin runtime.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("repos", help="List registered Tristan repositories.")
    list_parser.add_argument("--json", action="store_true")

    doctor = sub.add_parser("doctor", help="Check which repository distributions are installed.")
    doctor.add_argument("--json", action="store_true")

    plugins = sub.add_parser("plugins", help="List executable plugins discovered in this interpreter.")
    plugins.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="Run one plugin task.")
    run.add_argument("plugin")
    run.add_argument("task")
    run.add_argument("--payload-json", default="{}")

    pipeline = sub.add_parser("pipeline", help="Run plugin:task steps sequentially.")
    pipeline.add_argument("steps", nargs="+", help="Each step uses plugin:task syntax.")
    pipeline.add_argument("--payload-json", default="{}")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "repos":
        rows = [repo.to_dict() for repo in RepoRegistry().all()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                print(f"{row['key']:<12} {row['packaging_status']:<16} {row['full_name']}")
        return 0

    if args.command == "doctor":
        rows = [health.to_dict() for health in RepoRegistry().doctor()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                version = row["installed_version"] or "-"
                print(f"{row['key']:<12} {row['status']:<16} {version:<10} {row['message']}")
        return 0

    runtime = TristanRuntime(auto_discover=True)

    if args.command == "plugins":
        rows = [info.to_dict() for info in runtime.plugins()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                caps = ",".join(row["capabilities"])
                print(f"{row['name']:<24} {caps}")
        return 0

    if args.command == "run":
        print(_json(runtime.run(args.plugin, args.task, _payload(args.payload_json))))
        return 0

    steps: list[PipelineStep] = []
    for raw in args.steps:
        if ":" not in raw:
            raise SystemExit(f"Invalid step {raw!r}; expected plugin:task")
        plugin_name, task = raw.split(":", 1)
        steps.append(PipelineStep(plugin_name, task))
    print(_json(runtime.pipeline(steps, _payload(args.payload_json))))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
