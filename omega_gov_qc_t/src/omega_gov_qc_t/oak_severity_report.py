"""Aggregate local severity report for Ω-GOV-QC-T bundles.

The report summarizes local review priority across source, dataset and risk
sections. It does not publish anything and does not create issues remotely.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Tuple

from .oak_issue_severity import OAKIssueSeverityPolicy, SeverityDecision


PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass(frozen=True)
class OAKSeverityReport:
    """Aggregate local severity report."""

    schema: str
    generated_at: str
    source_bundle: str
    overall_priority: str
    decisions: Dict[str, SeverityDecision]
    oak_note: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "source_bundle": self.source_bundle,
            "overall_priority": self.overall_priority,
            "decisions": {name: decision.to_dict() for name, decision in self.decisions.items()},
            "oak_note": self.oak_note,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines: List[str] = [
            "# Ω-GOV-QC-T OAK Severity Report",
            "",
            f"Generated at: {self.generated_at}",
            f"Source bundle: `{self.source_bundle}`",
            f"Overall priority: `{self.overall_priority}`",
            "",
            "> This report is local workflow triage. It is not a final decision.",
            "",
            "## Decisions",
            "",
        ]
        for name, decision in self.decisions.items():
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- Priority: `{decision.priority}`",
                    f"- Status: `{decision.status}`",
                    f"- Note: {decision.oak_note}",
                    "",
                    "Reasons:",
                    "",
                ]
            )
            for reason in decision.reasons:
                lines.append(f"- `{reason}`")
            lines.append("")
        lines.extend(["## OAK note", "", self.oak_note, ""])
        return "\n".join(lines)


class OAKSeverityReportBuilder:
    """Build aggregate severity reports from local ExportBundle payloads."""

    def __init__(self, policy: OAKIssueSeverityPolicy | None = None) -> None:
        self.policy = policy or OAKIssueSeverityPolicy()

    def from_json_text(self, json_text: str) -> OAKSeverityReport:
        payload = json.loads(json_text)
        if not isinstance(payload, dict):
            raise ValueError("export bundle JSON must decode to an object")
        return self.from_payload(payload)

    def from_payload(self, payload: Dict[str, Any]) -> OAKSeverityReport:
        schema = str(payload.get("schema", ""))
        if schema != "omega_gov_qc_t.export_bundle.v0":
            raise ValueError(f"unsupported export bundle schema: {schema}")

        name = str(payload.get("name", "unnamed_bundle"))
        metadata = dict(payload.get("metadata", {}) or {})
        dataset_health = dict(metadata.get("dataset_health", {}) or {})
        sources = dict(payload.get("sources", {}) or {})
        risks = dict(payload.get("risks", {}) or {})

        decisions = {
            "source_registry": self.policy.source_registry(sources),
            "dataset_health": self.policy.dataset_health(dataset_health),
            "risk_register": self.policy.risk_register(risks),
        }
        overall = _overall_priority(tuple(decisions.values()))
        return OAKSeverityReport(
            schema="omega_gov_qc_t.oak_severity_report.v1.0",
            generated_at=datetime.now(timezone.utc).isoformat(),
            source_bundle=name,
            overall_priority=overall,
            decisions=decisions,
            oak_note=(
                "Severity priorities are local review workflow signals. They do not establish "
                "final findings, official decisions or remote publication readiness."
            ),
        )


def _overall_priority(decisions: Tuple[SeverityDecision, ...]) -> str:
    if not decisions:
        return "P3"
    return min((decision.priority for decision in decisions), key=lambda value: PRIORITY_ORDER.get(value, 99))
