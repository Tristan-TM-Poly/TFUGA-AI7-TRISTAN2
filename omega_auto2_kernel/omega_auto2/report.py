from __future__ import annotations

from .bench import run_suite
from .models import Workflow
from .telemetry import TelemetrySnapshot


def build_markdown_report(workflows: list[Workflow], telemetry: TelemetrySnapshot | None = None) -> str:
    suite = run_suite(workflows, telemetry)
    lines = [
        "# Ω-AUTO² Bench Report",
        "",
        f"Total: {suite['total']}",
        f"Passed: {suite['passed']}",
        f"Failed: {suite['failed']}",
        f"Pass rate: {suite['pass_rate']}",
        "",
        "| Workflow | Passed | Capacity | Proof | Dry-run |",
        "|---|---:|---:|---:|---:|",
    ]
    for result in suite["results"]:
        lines.append(
            f"| {result['workflow_id']} | {result['passed']} | {result['capacity_score']} | {result['proof_score']} | {result['dry_run_ok']} |"
        )
    lines.append("")
    lines.append("OAK note: this report is generated from local/draft data only.")
    return "\n".join(lines)
