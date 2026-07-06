"""Markdown report factory for Ω-GOV-QC-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from .evidence import EvidenceGraph
from .gov_graph import GovGraph
from .oak_gate import OAKReport
from .risk import RiskRegister
from .source_registry import SourceRegistry


@dataclass(frozen=True)
class GovReport:
    """A rendered public-sector analysis report."""

    title: str
    body_markdown: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_markdown(self) -> str:
        return self.body_markdown


class MarkdownReportFactory:
    """Render conservative Markdown reports from GovGraph artifacts."""

    def render_system_report(
        self,
        *,
        title: str,
        graph: GovGraph,
        sources: SourceRegistry,
        evidence: EvidenceGraph,
        risks: RiskRegister,
        oak_report: OAKReport,
        recommendations: List[str] | None = None,
    ) -> GovReport:
        recommendations = recommendations or []
        graph_quality = graph.quality_report()
        source_quality = sources.quality_report()
        evidence_quality = evidence.quality_report()
        risk_quality = risks.quality_report()

        lines: List[str] = [
            f"# {title}",
            "",
            "Status: OAK-safe analysis report",
            f"Generated at: {datetime.now(timezone.utc).isoformat()}",
            "",
            "> This report supports review and explanation. It is not final public authority.",
            "",
            "## 1. Graph summary",
            "",
            f"- Nodes: {graph_quality['node_count']}",
            f"- Edges: {graph_quality['edge_count']}",
            f"- Isolated nodes: {len(graph_quality['isolated_nodes'])}",
            "",
            "## 2. Source registry",
            "",
            f"- Sources: {source_quality['source_count']}",
            f"- Allowed: {source_quality['allowed_count']}",
            f"- Review required: {source_quality['review_required_count']}",
            f"- Blocked: {source_quality['blocked_count']}",
            "",
            "## 3. Evidence quality",
            "",
            f"- Evidence items: {evidence_quality['evidence_count']}",
            f"- Low confidence items: {len(evidence_quality['low_confidence'])}",
            f"- Items missing limitations: {len(evidence_quality['missing_limitations'])}",
            "",
            "## 4. Risk register",
            "",
            f"- Risks: {risk_quality['risk_count']}",
            f"- Blockers: {len(risk_quality['blockers'])}",
            f"- Bands: {risk_quality['by_band']}",
            "",
            "## 5. OAKGate",
            "",
            f"- Use case: {oak_report.use_case}",
            f"- Deployable: {oak_report.deployable}",
            f"- Classification: {oak_report.classification}",
            f"- Warning: {oak_report.warning}",
            "",
            "### Gate results",
            "",
        ]

        for gate in oak_report.gates:
            status = "PASS" if gate.passed else "BLOCK"
            lines.append(f"- {status}: {gate.name} — {gate.reason}")

        lines.extend(["", "## 6. Recommendations", ""])
        if recommendations:
            for item in recommendations:
                lines.append(f"- {item}")
        else:
            lines.append("- No recommendation was generated.")

        lines.extend(
            [
                "",
                "## 7. M- memory",
                "",
                "- Graph M-: " + str(graph_quality.get("m_minus", [])),
                "- Source M-: " + str(source_quality.get("m_minus", [])),
                "- Evidence M-: " + str(evidence_quality.get("m_minus", [])),
                "- Risk M-: " + str(risk_quality.get("m_minus", [])),
                "",
                "## 8. Limits",
                "",
                "- This report is generated from registered sources only.",
                "- Missing data can change conclusions.",
                "- High-impact use requires human authority and additional review.",
            ]
        )

        return GovReport(title=title, body_markdown="\n".join(lines))
