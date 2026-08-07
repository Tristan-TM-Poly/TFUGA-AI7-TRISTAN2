from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .resilient import audit_route_config, build_admission_report, scan_workflows


def _changed_files(args: argparse.Namespace) -> list[str]:
    rows = list(args.changed_file or [])
    if args.changed_files_path:
        rows.extend(
            line.strip()
            for line in Path(args.changed_files_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return rows


def _write(value: object, path: str | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-ci-admission",
        description="Dry-run workflow fanout analysis and route selection.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("--repository-root", default=".")
    scan.add_argument("--output")

    audit = sub.add_parser("audit-config")
    audit.add_argument("--repository-root", default=".")
    audit.add_argument("--config", required=True)
    audit.add_argument("--output")

    route = sub.add_parser("route")
    route.add_argument("--repository-root", default=".")
    route.add_argument("--config", required=True)
    route.add_argument("--changed-file", action="append")
    route.add_argument("--changed-files-path")
    route.add_argument("--output")
    route.add_argument("--github-output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "scan":
        workflows = scan_workflows(args.repository_root)
        result = {
            "schema": "omega-ci-workflow-scan/1.1",
            "workflows": [item.to_dict() for item in workflows],
            "workflow_parse_errors": [
                {
                    "workflow_path": item.path,
                    "warnings": [warning for warning in item.warnings if warning.startswith("parse_error:")],
                }
                for item in workflows
                if any(warning.startswith("parse_error:") for warning in item.warnings)
            ],
            "dry_run": True,
        }
    elif args.command == "audit-config":
        result = audit_route_config(args.repository_root, args.config)
    else:
        result = build_admission_report(
            args.repository_root,
            args.config,
            _changed_files(args),
        )
        if args.github_output:
            with Path(args.github_output).open("a", encoding="utf-8") as handle:
                handle.write(
                    "routes="
                    + json.dumps(
                        [item["route_id"] for item in result["selected_routes"]],
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                handle.write(
                    "validators="
                    + json.dumps(
                        [item["validator_id"] for item in result["selected_validators"]],
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                handle.write(f"report_digest={result['report_digest']}\n")
                handle.write(f"legacy_jobs={result['estimated_legacy_jobs']}\n")
                handle.write(f"replacement_jobs={result['estimated_replacement_jobs']}\n")
    _write(result, getattr(args, "output", None))
    if args.command == "audit-config":
        return 0 if result["valid"] else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
