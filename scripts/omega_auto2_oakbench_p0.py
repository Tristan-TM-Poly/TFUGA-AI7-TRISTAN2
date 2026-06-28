#!/usr/bin/env python3
"""Omega AUTO2 P0 OAKBench runner.

Runs synthetic benchmark cases through the integrated P0 spine and verifies
expected OAK outcomes. The runner is offline-only and uses local fixtures.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from omega_auto2_p0 import run_p0_pipeline

DEFAULT_SUITE = pathlib.Path("fixtures/omega_auto2/oakbench/p0_benchmark_suite.json")
DEFAULT_MMINUS = pathlib.Path("configs/omega_auto2_mminus_registry.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_mminus_registry(path: pathlib.Path = DEFAULT_MMINUS) -> dict[str, Any]:
    registry = load_json(path)
    entries = registry.get("entries", [])
    ids = [entry.get("id") for entry in entries]
    duplicate_ids = sorted({entry_id for entry_id in ids if ids.count(entry_id) > 1})
    return {
        "registry_id": registry.get("registry_id"),
        "entry_count": len(entries),
        "duplicate_ids": duplicate_ids,
        "modules": sorted({entry.get("module") for entry in entries if entry.get("module")}),
        "valid": len(entries) > 0 and not duplicate_ids,
    }


def run_case(case: dict[str, Any], repo_root: pathlib.Path) -> dict[str, Any]:
    fixture = repo_root / case["input_fixture"]
    request = load_json(fixture)
    report = run_p0_pipeline(request)
    status_ok = report.get("oak_status") == case.get("expected_oak_status")
    next_action_ok = report.get("next_action") == case.get("expected_next_action")
    return {
        "case_id": case.get("case_id"),
        "input_fixture": case.get("input_fixture"),
        "expected_oak_status": case.get("expected_oak_status"),
        "actual_oak_status": report.get("oak_status"),
        "expected_next_action": case.get("expected_next_action"),
        "actual_next_action": report.get("next_action"),
        "passed": bool(status_ok and next_action_ok),
        "module_statuses": report.get("module_statuses", {}),
        "residue_report": report.get("residue_report", {}),
    }


def run_suite(
    suite_path: pathlib.Path = DEFAULT_SUITE,
    mminus_path: pathlib.Path = DEFAULT_MMINUS,
    repo_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or pathlib.Path.cwd()
    suite = load_json(repo_root / suite_path if not suite_path.is_absolute() else suite_path)
    registry = load_mminus_registry(repo_root / mminus_path if not mminus_path.is_absolute() else mminus_path)
    cases = [run_case(case, repo_root) for case in suite.get("cases", [])]
    passed = sum(1 for case in cases if case["passed"])
    failed = len(cases) - passed
    oak_status = "PASS" if failed == 0 and registry["valid"] else "FAIL"
    return {
        "suite_id": suite.get("suite_id"),
        "oak_status": oak_status,
        "case_count": len(cases),
        "passed_count": passed,
        "failed_count": failed,
        "cases": cases,
        "mminus_registry": registry,
        "residue_report": {
            "case_failure_count": failed,
            "mminus_entry_count": registry["entry_count"],
            "mminus_duplicate_count": len(registry["duplicate_ids"]),
        },
        "external_actions_allowed": False,
        "production_use_allowed": False,
        "next_action": "ready_for_demo_pack_p0" if oak_status == "PASS" else "fix_oakbench_residues",
        "generated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default=str(DEFAULT_SUITE))
    parser.add_argument("--mminus", default=str(DEFAULT_MMINUS))
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run_suite(pathlib.Path(args.suite), pathlib.Path(args.mminus))
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["oak_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
