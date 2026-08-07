"""CLI for the Tristan multi-repository capability runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .adapter_forge import AdapterForge
from .bundle import BundlePlan
from .environment import EnvironmentMatrix
from .integration import DEFAULT_R07_LOCK
from .integration_r08 import DEFAULT_R08_LOCK
from .plugin import plugin as builtin_plugin
from .repo_registry import RepoRegistry
from .runtime import PipelineStep, TristanRuntime
from .supply_chain import SupplyChainOAK


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _payload(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("payload JSON must be an object")
    return parsed


def _runtime(*, discovery_mode: str = "lenient", expected_plugins: tuple[str, ...] = ()) -> TristanRuntime:
    runtime = TristanRuntime(
        auto_discover=True,
        discovery_mode=discovery_mode,
        expected_plugins=expected_plugins,
    )
    if not any(info.name == builtin_plugin.name for info in runtime.plugins()):
        runtime.register(builtin_plugin, source="builtin")
    return runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-tristan-runtime",
        description="Inspect, validate, bundle and execute Tristan capability repositories.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    repos = sub.add_parser("repos", help="List registered Tristan repositories.")
    repos.add_argument("--json", action="store_true")
    doctor = sub.add_parser("doctor", help="Check distributions and adapter maturity.")
    doctor.add_argument("--json", action="store_true")

    lock = sub.add_parser("integration-lock", help="Inspect immutable integration contracts.")
    lock.add_argument("--version", choices=("r07", "r08"), default="r08")
    lock.add_argument("--include-private-targets", action="store_true")
    bundle = sub.add_parser("bundle-plan", help="Render/materialize the reproducible bundle plan.")
    bundle.add_argument("--output-dir")
    bundle.add_argument("--include-private-extension", action="store_true")

    plugins = sub.add_parser("plugins", help="List executable plugins discovered in this interpreter.")
    plugins.add_argument("--json", action="store_true")
    discovery = sub.add_parser("discovery-report", help="Show loaded and failed plugin entry points.")
    discovery.add_argument("--mode", choices=("lenient", "strict", "oak-strict"), default="lenient")
    discovery.add_argument("--expect", action="append", default=[])

    capabilities = sub.add_parser("capabilities", help="Print the capability graph.")
    capabilities.add_argument("--json", action="store_true")
    schemas = sub.add_parser("schemas", help="Print registered payload schemas and compatibility edges.")
    schemas.add_argument("--json", action="store_true")
    compile_pipeline = sub.add_parser("compile-pipeline", help="Validate a capability chain before execution.")
    compile_pipeline.add_argument("capabilities", nargs="+")
    compile_pipeline.add_argument("--initial-schema", default="tristan.any")
    find_pipeline = sub.add_parser("find-pipeline", help="Search a schema-compatible capability path.")
    find_pipeline.add_argument("source_schema")
    find_pipeline.add_argument("target_schema")
    find_pipeline.add_argument("--max-steps", type=int, default=6)

    run = sub.add_parser("run", help="Run one plugin task.")
    run.add_argument("plugin")
    run.add_argument("task")
    run.add_argument("--payload-json", default="{}")
    run_cap = sub.add_parser("run-capability", help="Resolve and execute one capability.")
    run_cap.add_argument("capability")
    run_cap.add_argument("--plugin")
    run_cap.add_argument("--payload-json", default="{}")
    sandbox = sub.add_parser("run-sandboxed", help="Execute one capability in a bounded subprocess.")
    sandbox.add_argument("capability")
    sandbox.add_argument("--payload-json", default="{}")
    sandbox.add_argument("--timeout", type=float, default=10.0)
    sandbox.add_argument("--memory-mb", type=int, default=512)
    sandbox.add_argument("--allow", action="append", default=[])

    pipeline = sub.add_parser("pipeline", help="Run plugin:task steps sequentially.")
    pipeline.add_argument("steps", nargs="+")
    pipeline.add_argument("--payload-json", default="{}")
    cap_pipeline = sub.add_parser("cap-pipeline", help="Compile then run capability IDs sequentially.")
    cap_pipeline.add_argument("capabilities", nargs="+")
    cap_pipeline.add_argument("--payload-json", default="{}")
    cap_pipeline.add_argument("--initial-schema", default="tristan.any")

    adapter = sub.add_parser("adapter-plan", help="Statically inspect a local repository.")
    adapter.add_argument("path")
    adapter.add_argument("--plugin-name")

    sub.add_parser("environment", help="Print current and declared compatibility targets.")
    supply = sub.add_parser("supply-chain", help="Inventory loaded Tristan distributions and optionally verify wheel hashes.")
    supply.add_argument("--wheelhouse")
    supply.add_argument("--hash-manifest")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "repos":
        rows = [repo.to_dict() for repo in RepoRegistry().all()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                print(f"{row['key']:<12} {row['packaging_status']:<18} {row['full_name']}")
        return 0

    if args.command == "doctor":
        registry = RepoRegistry()
        rows = [health.to_dict() for health in registry.doctor()]
        payload = {"repositories": rows, "summary": registry.doctor_summary()}
        print(_json(payload) if args.json else "\n".join(
            [f"{row['key']:<12} {row['status']:<16} {(row['installed_version'] or '-'):<10} {row['message']}" for row in rows]
            + [_json(payload["summary"])]
        ))
        return 0

    if args.command == "integration-lock":
        if args.version == "r07":
            targets = DEFAULT_R07_LOCK.install_targets(include_private=args.include_private_targets)
            payload = {"lock": DEFAULT_R07_LOCK.to_dict(), "install_targets": list(targets)}
        else:
            payload = {
                "lock": DEFAULT_R08_LOCK.to_dict(),
                "public_install_targets": list(DEFAULT_R08_LOCK.public_install_targets()),
                "private_extension_targets": (
                    list(DEFAULT_R08_LOCK.private_extension_targets()) if args.include_private_targets else []
                ),
            }
        print(_json(payload))
        return 0

    if args.command == "bundle-plan":
        plan = BundlePlan()
        payload: dict[str, Any] = {
            "manifest": plan.manifest(include_private_extension=args.include_private_extension)
        }
        if args.output_dir:
            payload["files"] = plan.materialize(
                args.output_dir,
                include_private_extension=args.include_private_extension,
            ).to_dict()
        print(_json(payload))
        return 0

    if args.command == "adapter-plan":
        print(_json(AdapterForge().plan(Path(args.path), plugin_name=args.plugin_name).to_dict()))
        return 0

    if args.command == "environment":
        print(_json(EnvironmentMatrix().to_dict()))
        return 0

    if args.command == "discovery-report":
        runtime = _runtime(discovery_mode=args.mode, expected_plugins=tuple(args.expect))
        print(_json(runtime.discovery_report().to_dict()))
        return 0

    runtime = _runtime()

    if args.command == "plugins":
        rows = [info.to_dict() for info in runtime.plugins()]
        if args.json:
            print(_json(rows))
        else:
            for row in rows:
                print(f"{row['name']:<24} {row['version'] or '-':<10} {','.join(row['capabilities'])}")
        return 0

    if args.command == "capabilities":
        print(_json(runtime.capability_graph().to_dict()))
        return 0

    if args.command == "schemas":
        print(_json(runtime.schema_graph().to_dict()))
        return 0

    if args.command == "compile-pipeline":
        plan = runtime.pipeline_compiler().compile(args.capabilities, initial_schema=args.initial_schema)
        print(_json(plan.to_dict()))
        return 0

    if args.command == "find-pipeline":
        plan = runtime.pipeline_compiler().find_path(
            source_schema=args.source_schema,
            target_schema=args.target_schema,
            max_steps=args.max_steps,
        )
        print(_json(plan.to_dict()))
        return 0

    if args.command == "supply-chain":
        distributions = tuple(info.distribution for info in runtime.plugins() if info.distribution)
        report = SupplyChainOAK().report(
            distributions,
            wheelhouse=args.wheelhouse,
            hash_manifest=args.hash_manifest,
        )
        print(_json(report.to_dict()))
        return 0

    if args.command == "run":
        print(_json(runtime.run(args.plugin, args.task, _payload(args.payload_json))))
        return 0

    if args.command == "run-capability":
        execution = runtime.execute_capability(
            args.capability,
            _payload(args.payload_json),
            preferred_plugin=args.plugin,
        )
        print(_json(execution.to_dict()))
        return 0

    if args.command == "run-sandboxed":
        allowed = tuple(dict.fromkeys(["PURE", *args.allow]))
        result = runtime.execute_sandboxed(
            args.capability,
            _payload(args.payload_json),
            timeout_seconds=args.timeout,
            memory_mb=args.memory_mb,
            allowed_permissions=allowed,
        )
        print(_json(result.to_dict()))
        return 0

    if args.command == "cap-pipeline":
        print(_json(runtime.capability_pipeline(
            args.capabilities,
            _payload(args.payload_json),
            initial_schema=args.initial_schema,
        )))
        return 0

    steps: list[PipelineStep] = []
    for raw in args.steps:
        if ":" not in raw:
            raise SystemExit(f"Invalid step {raw!r}; expected plugin:task")
        plugin_name, task = raw.split(":", 1)
        steps.append(PipelineStep(plugin_name, task))
    print(_json(runtime.pipeline(steps, _payload(args.payload_json))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
