"""Municipal demo report builder for TristanGovGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .dataset_health import DatasetHealthEngine
from .evidence import EvidenceGraph, EvidenceItem
from .gov_graph import GovEdge, GovGraph, GovNode
from .json_exporter import ExportBundle, JsonExporter
from .oak_gate import OAKGate
from .opendata_ingestor import OpenDataIngestor
from .report_factory import MarkdownReportFactory
from .risk import RiskRegister, RiskTensor
from .source_registry import SourceRecord, SourceRegistry


DEMO_CSV = """id,name,type,region,updated_at
1,Demo Service,service,Demo Region,2026-07-06
2,Demo Dataset,dataset,Demo Region,2026-07-06
3,Demo Municipality,municipality,Demo Region,
"""


@dataclass(frozen=True)
class MunicipalDemoArtifacts:
    """Generated demo artifacts."""

    report_markdown: str
    bundle_json: str
    graph: GovGraph
    metadata: Dict[str, Any]


class MunicipalReportBuilder:
    """Build demo-only municipal reports from local example data."""

    def build_demo(self) -> MunicipalDemoArtifacts:
        source = SourceRecord(
            source_id="source:municipal_demo_local_csv",
            title="Municipal demo local CSV",
            kind="example",
            locator="embedded://omega_gov_qc_t.municipal_report.DEMO_CSV",
            permission="allowed",
            notes="Embedded example data only.",
        )
        sources = SourceRegistry()
        sources.add(source)

        ingestion = OpenDataIngestor().from_csv_text(
            dataset_id="dataset:municipal_demo",
            title="Municipal demo dataset",
            source=source,
            csv_text=DEMO_CSV,
        )
        health = DatasetHealthEngine().evaluate(ingestion.dataset)

        graph = GovGraph()
        graph.add_node(
            GovNode(
                node_id="municipality:demo",
                name="Demo Municipality",
                node_type="municipality",
                source=source.source_id,
                description="Demo-only municipality node.",
            )
        )
        graph.add_node(
            GovNode(
                node_id="dataset:municipal_demo",
                name="Municipal demo dataset",
                node_type="dataset",
                source=source.source_id,
                description="Dataset parsed from local example CSV.",
            )
        )
        graph.add_node(
            GovNode(
                node_id="risk:dataset_health_review",
                name="Dataset health review signal",
                node_type="risk",
                source=source.source_id,
                description="Review signal generated from missing or incomplete cells.",
            )
        )
        graph.add_edge(
            GovEdge(
                source_id="municipality:demo",
                target_id="dataset:municipal_demo",
                relation="publishes_or_uses_demo_dataset",
                evidence=source.source_id,
                confidence=0.8,
            )
        )
        graph.add_edge(
            GovEdge(
                source_id="dataset:municipal_demo",
                target_id="risk:dataset_health_review",
                relation="produces_review_signal",
                evidence="dataset_health_report",
                confidence=0.7,
            )
        )

        evidence = EvidenceGraph()
        evidence.add(
            EvidenceItem(
                evidence_id="evidence:municipal_demo_dataset_health",
                claim="The demo dataset has a computable health report.",
                source_id=source.source_id,
                status="structured_evidence",
                confidence=0.75,
                method="local CSV parsing and dataset health evaluation",
                limitations="Embedded example data only; not an official assessment.",
                counter_explanations=[
                    "Missing cells can be normal for optional fields.",
                    "Example rows do not represent a real municipality.",
                ],
            )
        )

        risks = RiskRegister()
        risks.add(
            RiskTensor(
                risk_id="risk:demo_dataset_health",
                name="Demo dataset health review",
                legal=0,
                privacy=0,
                security=0,
                fairness=0,
                human_impact=0,
                reversibility=5,
                evidence_quality=3,
                public_utility=3,
                notes="Example-only data quality signal.",
            )
        )

        oak_report = OAKGate().evaluate_context(
            use_case="municipal_demo_report",
            contains_personal_data=False,
            makes_sensitive_decision=False,
            source_is_authorized=True,
            human_review_required=False,
        )

        report = MarkdownReportFactory().render_system_report(
            title="Municipalite-OAK Demo Report",
            graph=graph,
            sources=sources,
            evidence=evidence,
            risks=risks,
            oak_report=oak_report,
            recommendations=[
                "Keep this report marked as demo-only.",
                "Replace embedded rows with authorized public sources before any pilot.",
                "Review missing fields before using dataset health signals in dashboards.",
            ],
        )

        bundle = ExportBundle(
            name="municipal_demo_bundle",
            graph=graph,
            sources=sources,
            evidence=evidence,
            risks=risks,
            metadata={
                "dataset_health": health.to_dict(),
                "ingestion_warnings": ingestion.warnings,
                "demo_only": True,
            },
        )

        return MunicipalDemoArtifacts(
            report_markdown=report.to_markdown(),
            bundle_json=JsonExporter().export_bundle(bundle),
            graph=graph,
            metadata={
                "dataset_health": health.to_dict(),
                "ingestion_warnings": ingestion.warnings,
                "oak_deployable": oak_report.deployable,
            },
        )
