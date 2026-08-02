"""Command-line interface for OAKGate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .gates import evaluate_claim
from .model import Claim, GateDecision, GateReport


def _load_claims(path: Path) -> list[Claim]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    if not all(isinstance(item, dict) for item in items):
        raise ValueError("Input must be a JSON object or a list of JSON objects")
    return [Claim.from_dict(item) for item in items]


def _render_markdown(reports: list[GateReport]) -> str:
    lines = ["# OAKGate report", ""]
    for report in reports:
        lines.extend(
            [
                f"## {report.claim_id}",
                "",
                f"**Decision:** `{report.decision.value}`",
                "",
            ]
        )
        if not report.findings:
            lines.append("No deterministic gate failure detected. Human review is still required before public release.")
            lines.append("")
            continue
        for finding in report.findings:
            lines.extend(
                [
                    f"- **{finding.severity.value} — {finding.code}:** {finding.message}",
                    f"  - Remediation: {finding.remediation}",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _exit_code(reports: list[GateReport]) -> int:
    if any(report.decision is GateDecision.BLOCK for report in reports):
        return 2
    if any(report.decision is GateDecision.WARN for report in reports):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oakgate",
        description="Evaluate epistemic, evidence, privacy, execution, and IP gates.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Evaluate one JSON claim or a JSON list")
    scan.add_argument("input", type=Path, help="Path to a claim JSON file")
    scan.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        dest="output_format",
    )
    scan.add_argument("--output", type=Path, help="Optional report output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        claims = _load_claims(args.input)
        reports = [evaluate_claim(claim) for claim in claims]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"oakgate: {exc}", file=sys.stderr)
        return 3

    if args.output_format == "json":
        rendered = json.dumps(
            [report.to_dict() for report in reports],
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    else:
        rendered = _render_markdown(reports)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return _exit_code(reports)


if __name__ == "__main__":
    raise SystemExit(main())
