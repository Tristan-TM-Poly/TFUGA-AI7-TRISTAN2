"""Markdown report factory for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from .evidence import EvidenceGraph
from .infra_graph import InfraGraph
from .maintenance import MaintenanceSignal
from .oak_security_gate import SecurityGateResult
from .resilience import ResilienceScenario
from .risk_tensor import InfraRiskTensor
from .source_registry import SourceRegistry


@dataclass(frozen=True)
class InfraReport:
    title: str
    generated_at: str
    markdown: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        return self.markdown


class MarkdownReportFactory:
    """Render OAK-safe infrastructure reports."""

    def render_system_report(
        self,
        *,
        title: str,
        graph: InfraGraph,
        sources: SourceRegistry,
        evidence: EvidenceGraph,
        risks: List[InfraRiskTensor],
        maintenance: List[MaintenanceSignal],
        scenarios: List[ResilienceScenario],
        security_gate: SecurityGateResult,
        public_safe: bool = True,
    ) -> InfraReport:
        generated_at = datetime.now(timezone.utc).isoformat()
        lines: List[str] = [
            f"# {title}",
            "",
            f"Generated at: `{generated_at}`",
            "",
            "> OAK note: This report is decision support, not a final engineering, legal, emergency or authority decision.",
            "",
            "## Security Gate",
            "",
            f"- Status: `{security_gate.status}`",
            f"- Publishable: `{security_gate.publishable}`",
            f"- Blockers: `{', '.join(security_gate.blockers) if security_gate.blockers else 'none'}`",
            f"- Warnings: `{', '.join(security_gate.warnings) if security_gate.warnings else 'none'}`",
            "",
            "## Graph Summary",
            "",
        ]
        quality = graph.quality_report()
        lines.extend([f"- Assets: {quality['asset_count']}", f"- Dependencies: {quality['dependency_count']}", f"- Sensitive assets: {quality['sensitive_asset_count']}", ""])

        lines.extend(["## Source Registry", ""])
        source_quality = sources.quality_report()
        lines.extend([f"- Sources: {source_quality['source_count']}", f"- Allowed: {len(source_quality['allowed'])}", f"- Review required: {len(source_quality['review_required'])}", f"- Blocked: {len(source_quality['blocked'])}", ""])

        lines.extend(["## Evidence", ""])
        evidence_quality = evidence.quality_report()
        lines.extend([f"- Evidence items: {evidence_quality['evidence_count']}", f"- Status counts: `{evidence_quality['status_counts']}`", ""])

        lines.extend(["## Risk Tensors", ""])
        if risks:
            for risk in risks:
                lines.append(f"- `{risk.asset_id}`: band `{risk.band}`, pressure `{risk.pressure}`, maintenance priority `{risk.maintenance_priority}`")
        else:
            lines.append("- No risk tensors provided.")
        lines.append("")

        lines.extend(["## Maintenance", ""])
        if maintenance:
            for signal in maintenance:
                lines.append(f"- `{signal.asset_id}`: band `{signal.band}`, priority `{signal.priority_score}`, needs evidence `{signal.needs_more_evidence}`")
        else:
            lines.append("- No maintenance signals provided.")
        lines.append("")

        lines.extend(["## Resilience Scenarios", ""])
        if scenarios:
            for scenario in scenarios:
                payload = scenario.to_dict(public_safe=public_safe)
                lines.append(f"- `{scenario.name}`: kind `{scenario.kind}`, band `{payload['band']}`, affected asset count `{payload['affected_asset_count']}`")
        else:
            lines.append("- No resilience scenarios provided.")
        lines.append("")

        lines.extend(["## Limits", "", "- Demo or authorized data only by default.", "- Public summaries must not expose sensitive details.", "- Human review required for real assets and real decisions.", "- Signals are not final judgments.", ""])

        return InfraReport(
            title=title,
            generated_at=generated_at,
            markdown="\n".join(lines),
            metadata={"public_safe": public_safe, "security_gate": security_gate.to_dict()},
        )
