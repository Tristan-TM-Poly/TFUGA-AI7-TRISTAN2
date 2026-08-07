"""CLI for the Tristan multi-repository Python runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .adapter_forge import AdapterForge
from .plugin import plugin as builtin_plugin
from .repo_registry import RepoRegistry
from .runtime import PipelineStep, TristanRuntime


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _payload(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("payload JSON must be an object")
    return parsed


def _runtime() -> TristanRuntime:
    runtime = TristanRuntime(auto_discover=True)
    if not any(info.name == builtin_plugin.name for info in runtime.plugins()):
        runtime.register(builtin_plugin, source="builtin")
    return runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-tristan-runtime", description="Inspect and execute Tristan repositories through one capability runtime.")
    sub = parser.add_subparsers(dest="command", required=True)
    repos = sub.add_parser("repos", help="List registered Tristan repositories.")
    repos.add_argument("--json", action="store_true")
    doctor = sub.add_parser("doctor", help="Check repository distributions and packaging maturity.")
    doctor.add_argument("--json", action="store_true")
    plugins = sub.add_parser("plugins", help="List executable plugins discovered in this interpreter.")
    plugins.add_argument("--json", action="store_true")
    capabilities = sub.add_parser("capabilities", help="Print the capability graph.")
    capabilities.add_argument("--json", action="store_true")
    run = sub.add_parser("run", help="Run one plugin task.")
    run.add_argument("plugin")
    run.add_argument("task")
    run.add_argument("--payload-json", default="{}")
    run_cap = sub.add_parser("run-capability", help="Resolve and execute one capability.")
    run_cap.add_argument("capability")
    run_cap.add_argument("--plugin")
    run_cap.add_argument("--payload-json", default="{}")
    pipeline = sub.add_parser("pipeline", help="Run plugin:task steps sequentially.")
    pipeline.add_argument("steps", nargs="+", help="Each step uses plugin:task syntax.")
    pipeline.add_argument("--payload-json", default="{}")
    cap_pipeline = sub.add_parser("cap-pipeline", help="Run capability IDs sequentially.")
    cap_pipeline.add_argument("capabilities", nargs="+")
    cap_pipeline.add_argument("--payload-json", default="{}")
    adapter = sub.add_parser("adapter-plan", help="Statically inspect a local repository.")
    adapter.add_argument("path")
    adapter.add_argument("--plugin-name")
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
            print(_json({"repositories": rows, "summary": RepoRegistry().doctor_summary()}))
        else:
            for row in rows:
                version = row["installed_version"] or "-"
                print(f"{row['key']:<12} {row['status']:<16} {version:<10} {row['message']}")
            print(_json(RepoRegistry().doctor_summary()))
        return 0
    if args.command == "adapter-plan":
        print(_json(AdapterForge().plan(Path(args.path), plugin_name=args.plugin_name).to_dict()))
        return 0
    runtime = _runtime()
    if args.command == "plugins":
        rows = [info.to_dict() for info in runtime.plugins()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                print(f"{row['name']:<24} {','.join(row['capabilities'])}")
        return 0
    if args.command == "capabilities":
        print(_json(runtime.capability_graph().to_dict()))
        return 0
    if args.command == "run":
        print(_json(runtime.run(args.plugin, args.task, _payload(args.payload_json))))
        return 0
    if args.command == "run-capability":
        result = runtime.execute_capability(args.capability, _payload(args.payload_json), preferred_plugin=args.plugin)
        print(_json(result.to_dict()))
        return 0
    if args.command == "cap-pipeline":
        print(_json(runtime.capability_pipeline(args.capabilities, _payload(args.payload_json))))
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
