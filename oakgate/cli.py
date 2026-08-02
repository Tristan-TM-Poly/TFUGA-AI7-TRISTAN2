"""Command-line interface for OAKGate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import RulePack, load_rule_pack
from .gates import evaluate_claim
from .model import GateDecision, GateReport
from .provenance import claim_provenance_hash
from .sarif import reports_to_github_annotations, reports_to_sarif
from .scanner import expand_inputs, load_scanned_claims


def _render_markdown(reports: list[GateReport]) -> str:
    lines = ["# OAKGate report", ""]
    for report in reports:
        lines.extend(
            [
                f"## {report.claim_id}",
                "",
                f"**Decision:** `{report.decision.value}`",
            ]
        )
        if report.source is not None:
            lines.append(
                f"**Source:** `{report.source.path}:{report.source.start_line}"
                f"-{report.source.end_line}`"
            )
        lines.extend(
            [
                f"**U² confidence debt:** `{report.confidence_debt:.2f}`",
                f"**Justified confidence cap:** `{report.justified_confidence:.2f}`",
                "",
            ]
        )
        if not report.findings:
            lines.append(
                "No deterministic gate failure detected. Human review is still "
                "required before public release."
            )
            lines.append("")
            continue
        for finding in report.findings:
            lines.extend(
                [
                    f"- **{finding.severity.value} — {finding.code}:** "
                    f"{finding.message}",
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


def _load_reports(
    inputs: list[Path],
    *,
    recursive: bool,
    rule_pack: RulePack | None,
) -> tuple[list[GateReport], list[tuple[str, str]]]:
    reports: list[GateReport] = []
    hashes: list[tuple[str, str]] = []
    for path in expand_inputs(inputs, recursive=recursive):
        for scanned in load_scanned_claims(path):
            reports.append(
                evaluate_claim(
                    scanned.claim,
                    rule_pack=rule_pack,
                    source=scanned.source,
                )
            )
            hashes.append(
                (scanned.claim.claim_id, claim_provenance_hash(scanned.claim))
            )
    return reports, hashes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oakgate",
        description=(
            "Evaluate epistemic, evidence, privacy, execution, provenance, "
            "uncertainty, and IP gates."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser(
        "scan",
        help="Evaluate JSON claims or fenced Markdown oak-claim blocks",
    )
    scan.add_argument(
        "inputs",
        type=Path,
        nargs="+",
        help="Claim JSON/Markdown files, or directories with --recursive",
    )
    scan.add_argument(
        "--format",
        choices=("json", "markdown", "sarif", "github"),
        default="markdown",
        dest="output_format",
    )
    scan.add_argument("--output", type=Path, help="Optional report output path")
    scan.add_argument("--rules", type=Path, help="Optional JSON rule pack")
    scan.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan .json/.md/.markdown files in directories",
    )

    hash_parser = subparsers.add_parser(
        "hash",
        help="Compute canonical SHA-256 provenance hashes for claims",
    )
    hash_parser.add_argument("inputs", type=Path, nargs="+")
    hash_parser.add_argument("--recursive", action="store_true")
    hash_parser.add_argument("--output", type=Path)

    return parser


def _write_or_print(rendered: str, output: Path | None) -> None:
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        rule_pack = load_rule_pack(args.rules) if getattr(args, "rules", None) else None
        reports, hashes = _load_reports(
            args.inputs,
            recursive=args.recursive,
            rule_pack=rule_pack,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"oakgate: {exc}", file=sys.stderr)
        return 3

    if args.command == "hash":
        rendered = (
            json.dumps(
                [
                    {"claim_id": claim_id, "provenance_hash": digest}
                    for claim_id, digest in hashes
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        _write_or_print(rendered, args.output)
        return 0

    if args.output_format == "json":
        rendered = (
            json.dumps(
                [report.to_dict() for report in reports],
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
    elif args.output_format == "sarif":
        rendered = (
            json.dumps(reports_to_sarif(reports), ensure_ascii=False, indent=2) + "\n"
        )
    elif args.output_format == "github":
        rendered = reports_to_github_annotations(reports)
    else:
        rendered = _render_markdown(reports)

    _write_or_print(rendered, args.output)
    return _exit_code(reports)


if __name__ == "__main__":
    raise SystemExit(main())
