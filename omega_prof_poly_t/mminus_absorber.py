"""M⁻ registry for Omega absorber failure memory.

The registry stores negative evidence and failure modes emitted by ingestion,
PDF extraction, OCR, claims, source policies, and canonization. It is append-only
by convention and intentionally simple JSONL so it can survive tool changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class MMinusEntry:
    timestamp_utc: str
    source: str
    kind: str
    severity: str
    description: str
    evidence: dict
    action: str
    status: str = "open"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_entry(path: str | Path, entry: MMinusEntry) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return target


def load_entries(path: str | Path) -> list[MMinusEntry]:
    target = Path(path)
    if not target.exists():
        return []
    entries: list[MMinusEntry] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        entries.append(MMinusEntry(**payload))
    return entries


def entries_from_oak_report(oak_report_path: str | Path) -> list[MMinusEntry]:
    path = Path(oak_report_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    entries: list[MMinusEntry] = []
    for warning in report.get("warnings", []):
        entries.append(
            MMinusEntry(
                timestamp_utc=now_utc(),
                source=str(path),
                kind="oak_warning",
                severity="medium",
                description=str(warning),
                evidence={"oak_report": str(path)},
                action="route_to_extraction_or_policy_fix_before_canonization",
            )
        )
    blocked = int(report.get("blocked_or_review_claims", 0) or 0)
    if blocked:
        entries.append(
            MMinusEntry(
                timestamp_utc=now_utc(),
                source=str(path),
                kind="blocked_or_review_claims",
                severity="high",
                description=f"{blocked} claims require OAK review before publication or canonization",
                evidence={"blocked_or_review_claims": blocked},
                action="keep_private_and_create_review_packets",
            )
        )
    if report.get("publishable") is not False:
        entries.append(
            MMinusEntry(
                timestamp_utc=now_utc(),
                source=str(path),
                kind="unsafe_publishable_flag",
                severity="critical",
                description="Absorber output is expected to be publishable=false by default",
                evidence={"publishable": report.get("publishable")},
                action="force_publishable_false_until_IP_privacy_safety_review",
            )
        )
    return entries


def summarize_entries(entries: Sequence[MMinusEntry]) -> dict:
    by_kind: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for entry in entries:
        by_kind[entry.kind] = by_kind.get(entry.kind, 0) + 1
        by_severity[entry.severity] = by_severity.get(entry.severity, 0) + 1
    return {
        "entries": len(entries),
        "by_kind": dict(sorted(by_kind.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "open": sum(1 for entry in entries if entry.status == "open"),
    }


def render_summary_markdown(entries: Sequence[MMinusEntry]) -> str:
    summary = summarize_entries(entries)
    lines = ["# Omega Absorber M⁻ Registry", "", f"- entries: `{summary['entries']}`", f"- open: `{summary['open']}`", "", "## By severity"]
    lines.extend(f"- `{key}`: {value}" for key, value in summary["by_severity"].items())
    lines.append("")
    lines.append("## By kind")
    lines.extend(f"- `{key}`: {value}" for key, value in summary["by_kind"].items())
    if entries:
        lines.append("")
        lines.append("## Latest")
        for entry in entries[-10:]:
            lines.append(f"- `{entry.severity}` `{entry.kind}` — {entry.description}")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-mminus-absorb", description="Maintain absorber M-minus registry")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest-oak")
    ingest.add_argument("oak_report")
    ingest.add_argument("--registry", default="generated/m_minus_absorber.jsonl")
    summary = sub.add_parser("summary")
    summary.add_argument("--registry", default="generated/m_minus_absorber.jsonl")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> str:
    args = build_parser().parse_args(argv)
    if args.command == "ingest-oak":
        entries = entries_from_oak_report(args.oak_report)
        for entry in entries:
            append_entry(args.registry, entry)
        return f"mminus_entries_appended={len(entries)} registry={args.registry}\n"
    return render_summary_markdown(load_entries(args.registry))


def main() -> None:
    sys.stdout.write(run_cli())


if __name__ == "__main__":
    main()
