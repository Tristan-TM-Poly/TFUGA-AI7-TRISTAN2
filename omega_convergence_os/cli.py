from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .analyzer import build_branch_dna, compare_branch_dna
from .models import BranchDNA, Conflict, ConflictKind, FileChange, MergePlan, Severity
from .planner import build_merge_plan
from .receipt import build_merge_receipt


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _dna_from_dict(payload: dict[str, Any]) -> BranchDNA:
    return BranchDNA(
        branch=payload["branch"],
        base_sha=payload["base_sha"],
        head_sha=payload["head_sha"],
        files=tuple(FileChange(**item) for item in payload.get("files", [])),
        public_symbols={key: tuple(value) for key, value in payload.get("public_symbols", {}).items()},
        scripts=payload.get("scripts", {}),
        workflow_permissions=payload.get("workflow_permissions", {}),
        epistemic_statuses=payload.get("epistemic_statuses", {}),
        claims=tuple(payload.get("claims", [])),
        tests=tuple(payload.get("tests", [])),
        risks=tuple(payload.get("risks", [])),
    )


def _conflict_from_dict(payload: dict[str, Any]) -> Conflict:
    return Conflict(
        kind=ConflictKind(payload["kind"]),
        severity=Severity(payload["severity"]),
        key=payload["key"],
        message=payload["message"],
        base_value=payload.get("base_value"),
        head_value=payload.get("head_value"),
        recommended_action=payload.get("recommended_action", "review"),
        evidence=tuple(payload.get("evidence", [])),
    )


def _plan_from_dict(payload: dict[str, Any]) -> MergePlan:
    return MergePlan(
        base_sha=payload["base_sha"],
        head_sha=payload["head_sha"],
        strategy_by_path=payload.get("strategy_by_path", {}),
        conflicts=tuple(_conflict_from_dict(item) for item in payload.get("conflicts", [])),
        required_tests=tuple(payload.get("required_tests", [])),
        preservation_paths=tuple(payload.get("preservation_paths", [])),
        rollback_steps=tuple(payload.get("rollback_steps", [])),
        verdict=payload["verdict"],
        automatic_merge_allowed=False,
    )


def command_branch_dna(args: argparse.Namespace) -> int:
    payload = _read_json(args.input)
    contents = payload.get("file_contents", {})
    dna = build_branch_dna(
        branch=payload["branch"],
        base_sha=payload["base_sha"],
        head_sha=payload["head_sha"],
        file_contents=contents,
        statuses=payload.get("statuses", {}),
        tests=payload.get("tests", []),
        claims=payload.get("claims", []),
        risks=payload.get("risks", []),
    )
    result = dna.canonical_dict()
    result["sha256"] = dna.digest()
    _write(result, args.output)
    return 0


def command_compare(args: argparse.Namespace) -> int:
    base = _dna_from_dict(_read_json(args.base))
    head = _dna_from_dict(_read_json(args.head))
    conflicts = compare_branch_dna(base, head)
    _write({"conflicts": [asdict(item) for item in conflicts]}, args.output)
    return 2 if any(item.severity is Severity.CRITICAL for item in conflicts) else 0


def command_plan(args: argparse.Namespace) -> int:
    payload = _read_json(args.input)
    conflicts = tuple(_conflict_from_dict(item) for item in payload.get("conflicts", []))
    plan = build_merge_plan(
        base_sha=payload["base_sha"],
        head_sha=payload["head_sha"],
        changed_paths=payload.get("changed_paths", []),
        conflicts=conflicts,
        declared_tests=payload.get("declared_tests", []),
    )
    _write(asdict(plan), args.output)
    return 2 if plan.verdict == "BLOCKED_SECURITY_OR_POLICY" else 0


def command_receipt(args: argparse.Namespace) -> int:
    payload = _read_json(args.input)
    dna = _dna_from_dict(payload["branch_dna"])
    plan = _plan_from_dict(payload["plan"])
    receipt = build_merge_receipt(
        branch_dna=dna,
        plan=plan,
        result_sha=payload.get("result_sha"),
        completed_tests=tuple(payload.get("completed_tests", [])),
        artifacts=tuple(payload.get("artifacts", [])),
        known_residues=tuple(payload.get("known_residues", [])),
        timestamp=payload.get("timestamp"),
    )
    result = receipt.canonical_dict()
    result["receipt_sha256"] = receipt.digest()
    _write(result, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-convergence")
    sub = parser.add_subparsers(dest="command", required=True)

    dna = sub.add_parser("branch-dna", help="compile a deterministic Branch DNA JSON")
    dna.add_argument("input")
    dna.add_argument("--output")
    dna.set_defaults(func=command_branch_dna)

    compare = sub.add_parser("compare", help="compare two Branch DNA JSON files")
    compare.add_argument("base")
    compare.add_argument("head")
    compare.add_argument("--output")
    compare.set_defaults(func=command_compare)

    plan = sub.add_parser("plan", help="compile an OAK-safe dry-run merge plan")
    plan.add_argument("input")
    plan.add_argument("--output")
    plan.set_defaults(func=command_plan)

    receipt = sub.add_parser("receipt", help="build an immutable merge receipt")
    receipt.add_argument("input")
    receipt.add_argument("--output")
    receipt.set_defaults(func=command_receipt)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
