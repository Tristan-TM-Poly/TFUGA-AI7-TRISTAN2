"""SARIF and GitHub annotation rendering for OAKGate reports."""

from __future__ import annotations

from typing import Any

from .model import GateDecision, GateReport


_LEVEL = {
    GateDecision.PASS: "note",
    GateDecision.WARN: "warning",
    GateDecision.BLOCK: "error",
}


def reports_to_sarif(reports: list[GateReport]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for report in reports:
        for finding in report.findings:
            rules.setdefault(
                finding.code,
                {
                    "id": finding.code,
                    "name": finding.code,
                    "shortDescription": {"text": finding.message},
                    "help": {"text": finding.remediation},
                },
            )
            result: dict[str, Any] = {
                "ruleId": finding.code,
                "level": _LEVEL[finding.severity],
                "message": {
                    "text": (
                        f"{report.claim_id}: {finding.message} "
                        f"Remediation: {finding.remediation}"
                    )
                },
            }
            if report.source is not None:
                result["locations"] = [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": report.source.path},
                            "region": {
                                "startLine": report.source.start_line,
                                "endLine": report.source.end_line,
                            },
                        }
                    }
                ]
            results.append(result)

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "OAKGate",
                        "version": "0.2.0",
                        "informationUri": "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def reports_to_github_annotations(reports: list[GateReport]) -> str:
    lines: list[str] = []
    for report in reports:
        for finding in report.findings:
            command = "error" if finding.severity is GateDecision.BLOCK else "warning"
            location = ""
            if report.source is not None:
                location = (
                    f" file={report.source.path},"
                    f"line={report.source.start_line},"
                    f"endLine={report.source.end_line},"
                )
            title = f"OAKGate {finding.code}"
            message = (
                f"{report.claim_id}: {finding.message} "
                f"Remediation: {finding.remediation}"
            )
            escaped = (
                message.replace("%", "%25")
                .replace("\r", "%0D")
                .replace("\n", "%0A")
            )
            lines.append(f"::{command}{location}title={title}::{escaped}")
    return "\n".join(lines) + ("\n" if lines else "")
