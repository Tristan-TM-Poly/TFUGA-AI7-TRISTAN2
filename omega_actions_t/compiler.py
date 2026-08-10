"""Deterministic CI Intermediate Representation compiler for Ω-ACTIONS-T∞ R0.7."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CHECKOUT_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"
UPLOAD_ARTIFACT_SHA = "ea165f8d65b6e75b540449e92b4886f43607fa02"
_SAFE_PERMISSION_LEVELS = {"none", "read"}
_JOB_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def _quote(value: Any) -> str:
    text = str(value)
    if text == "":
        return "''"
    if re.fullmatch(r"[A-Za-z0-9_./${}@:+-]+", text):
        return text
    return "'" + text.replace("'", "''") + "'"


def validate_ir(ir: dict[str, Any], *, allow_write_permissions: bool = False) -> None:
    if not isinstance(ir, dict):
        raise ValueError("CI IR must be a mapping")
    jobs = ir.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("CI IR requires a non-empty jobs list")
    seen: set[str] = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("every job must be a mapping")
        job_id = str(job.get("id") or "")
        if not _JOB_ID.fullmatch(job_id):
            raise ValueError(f"invalid job id: {job_id!r}")
        if job_id in seen:
            raise ValueError(f"duplicate job id: {job_id}")
        seen.add(job_id)
        timeout = int(job.get("timeout_minutes") or 0)
        if timeout <= 0:
            raise ValueError(f"job {job_id} requires positive timeout_minutes")
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"job {job_id} requires steps")
    for job in jobs:
        for need in job.get("needs") or []:
            if need not in seen:
                raise ValueError(f"job {job['id']} references unknown need {need}")
    permissions = ir.get("permissions", {"contents": "read"})
    if not isinstance(permissions, dict):
        raise ValueError("permissions must be a mapping")
    if not allow_write_permissions:
        unsafe = {key: value for key, value in permissions.items() if str(value) not in _SAFE_PERMISSION_LEVELS}
        if unsafe:
            raise ValueError(f"write/elevated permissions require explicit opt-in: {unsafe}")
    triggers = ir.get("on", {"workflow_dispatch": {}})
    if not isinstance(triggers, dict):
        raise ValueError("on must be a mapping")


def _compile_filter_values(lines: list[str], key: str, values: list[Any], indent: str) -> None:
    lines.append(f"{indent}{key}:")
    for value in values:
        lines.append(f"{indent}  - {_quote(value)}")


def _compile_trigger(lines: list[str], trigger: str, config: Any, *, workflow_path: str) -> None:
    if config is None or config == {}:
        lines.append(f"  {trigger}:")
        return
    if not isinstance(config, dict):
        raise ValueError(f"trigger {trigger} must be a mapping")
    lines.append(f"  {trigger}:")
    for key in ("branches", "branches-ignore", "paths", "paths-ignore"):
        if key not in config:
            continue
        values = list(config.get(key) or [])
        if key == "paths" and workflow_path not in values:
            values.append(workflow_path)
        _compile_filter_values(lines, key, values, "    ")
    unknown = set(config) - {"branches", "branches-ignore", "paths", "paths-ignore"}
    if unknown:
        raise ValueError(f"unsupported trigger fields for {trigger}: {sorted(unknown)}")


def _compile_step(step: dict[str, Any]) -> list[str]:
    if not isinstance(step, dict):
        raise ValueError("step must be a mapping")
    kind = str(step.get("kind") or "run")
    name = step.get("name")
    lines: list[str] = []
    if name:
        lines.append(f"      - name: {_quote(name)}")
        prefix = "        "
    else:
        prefix = "      - "

    if kind == "checkout":
        lines.append(f"{prefix}uses: actions/checkout@{CHECKOUT_SHA}")
        if name:
            lines.append(f"{prefix}with:")
            lines.append(f"{prefix}  persist-credentials: false")
        return lines
    if kind == "setup-python":
        lines.append(f"{prefix}uses: actions/setup-python@{SETUP_PYTHON_SHA}")
        if name:
            lines.append(f"{prefix}with:")
            if step.get("python_version"):
                lines.append(f"{prefix}  python-version: {_quote(step['python_version'])}")
            if step.get("cache"):
                lines.append(f"{prefix}  cache: {_quote(step['cache'])}")
        return lines
    if kind == "upload-artifact":
        lines.append(f"{prefix}uses: actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}")
        if name:
            lines.append(f"{prefix}with:")
            lines.append(f"{prefix}  name: {_quote(step.get('artifact_name') or 'artifact')}")
            lines.append(f"{prefix}  path: {_quote(step.get('path') or '.')}")
            lines.append(f"{prefix}  if-no-files-found: error")
            if step.get("retention_days"):
                lines.append(f"{prefix}  retention-days: {int(step['retention_days'])}")
        return lines
    if kind != "run":
        raise ValueError(f"unsupported step kind: {kind}")
    command = str(step.get("run") or "")
    if not command:
        raise ValueError("run step requires command")
    if "\n" in command:
        lines.append(f"{prefix}run: |")
        for command_line in command.splitlines():
            lines.append(f"{prefix}  {command_line}")
    else:
        lines.append(f"{prefix}run: {command}")
    return lines


def compile_workflow(
    ir: dict[str, Any],
    *,
    workflow_path: str = ".github/workflows/generated-ci.yml",
    allow_write_permissions: bool = False,
) -> str:
    validate_ir(ir, allow_write_permissions=allow_write_permissions)
    lines = [f"name: {_quote(ir.get('name') or 'Generated CI')}", "", "on:"]
    triggers = ir.get("on", {"workflow_dispatch": {}})
    for trigger, config in triggers.items():
        _compile_trigger(lines, str(trigger), config, workflow_path=workflow_path)

    lines += ["", "permissions:"]
    permissions = ir.get("permissions", {"contents": "read"})
    for scope, level in sorted(permissions.items()):
        lines.append(f"  {scope}: {level}")

    concurrency = ir.get("concurrency")
    if concurrency:
        if not isinstance(concurrency, dict):
            raise ValueError("concurrency must be a mapping")
        lines += ["", "concurrency:"]
        lines.append(f"  group: {_quote(concurrency.get('group') or '${{ github.workflow }}-${{ github.ref }}')}")
        lines.append(f"  cancel-in-progress: {'true' if concurrency.get('cancel_in_progress', True) else 'false'}")

    lines += ["", "jobs:"]
    for job in ir["jobs"]:
        job_id = str(job["id"])
        lines.append(f"  {job_id}:")
        if job.get("name"):
            lines.append(f"    name: {_quote(job['name'])}")
        if job.get("needs"):
            needs = list(job["needs"])
            if len(needs) == 1:
                lines.append(f"    needs: {needs[0]}")
            else:
                lines.append("    needs:")
                for need in needs:
                    lines.append(f"      - {need}")
        lines.append(f"    runs-on: {_quote(job.get('runs_on') or 'ubuntu-latest')}")
        lines.append(f"    timeout-minutes: {int(job['timeout_minutes'])}")
        strategy = job.get("strategy")
        if strategy:
            if not isinstance(strategy, dict):
                raise ValueError(f"strategy for {job_id} must be a mapping")
            lines.append("    strategy:")
            if "fail_fast" in strategy:
                lines.append(f"      fail-fast: {'true' if strategy['fail_fast'] else 'false'}")
            if strategy.get("max_parallel") is not None:
                lines.append(f"      max-parallel: {int(strategy['max_parallel'])}")
            matrix = strategy.get("matrix")
            if matrix:
                lines.append("      matrix:")
                for axis, values in matrix.items():
                    rendered = ", ".join(_quote(value) for value in values)
                    lines.append(f"        {axis}: [{rendered}]")
        lines.append("    steps:")
        for step in job["steps"]:
            lines.extend(_compile_step(step))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-compile", description="Compile OAK-safe CI IR to deterministic GitHub Actions YAML.")
    parser.add_argument("input", help="CI IR JSON")
    parser.add_argument("--workflow-path", default=".github/workflows/generated-ci.yml")
    parser.add_argument("--out")
    parser.add_argument("--allow-write-permissions", action="store_true")
    args = parser.parse_args(argv)
    ir = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = compile_workflow(ir, workflow_path=args.workflow_path, allow_write_permissions=args.allow_write_permissions)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
