"""Safe demo builder for InfrastructureGraph Quebec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .asset_model import AssetNode
from .evidence import EvidenceGraph, EvidenceItem
from .infra_graph import DependencyEdge, InfraGraph
from .json_exporter import InfraExportBundle, JsonExporter
from .maintenance import MaintenanceSignal
from .oak_security_gate import OAKSecurityGate
from .report_factory import MarkdownReportFactory
from .resilience import ResilienceScenario
from .risk_tensor import InfraRiskTensor
from .source_registry import SourceRecord, SourceRegistry


@dataclass(frozen=True)
class InfraDemoArtifacts:
    report_markdown: str
    bundle_json: str
    metadata: Dict[str, Any]


def build_demo_artifacts() -> InfraDemoArtifacts:
    """Build a deterministic public-safe demo with fictional/generalized assets."""

    graph = InfraGraph()
    graph.add_asset(
        AssetNode(
            asset_id="asset:demo_bridge",
            name="Demo Local Bridge",
            sector="transport",
            owner_type="municipal",
            region="Demo Region",
            municipality="Demo Municipality",
            visibility="public",
            criticality=3,
            public_dependency=3,
            condition_status="review",
            notes="Generalized demo bridge; no real location.",
        )
    )
    graph.add_asset(
        AssetNode(
            asset_id="asset:demo_water_facility",
            name="Demo Water Facility",
            sector="water",
            owner_type="municipal",
            region="Demo Region",
            municipality="Demo Municipality",
            visibility="review",
            criticality=4,
            public_dependency=5,
            condition_status="unknown",
            notes="Generalized review-only demo facility.",
        )
    )
    graph.add_asset(
        AssetNode(
            asset_id="asset:demo_school",
            name="Demo School Building",
            sector="education",
            owner_type="public",
            region="Demo Region",
            municipality="Demo Municipality",
            visibility="public",
            criticality=2,
            public_dependency=3,
            condition_status="planned",
        )
    )
    graph.add_dependency(
        DependencyEdge(
            source_asset_id="asset:demo_school",
            target_asset_id="asset:demo_bridge",
            kind="depends_on",
            confidence=0.6,
            visibility="public",
            notes="Generalized access dependency for demo only.",
        )
    )

    sources = SourceRegistry()
    sources.add(
        SourceRecord(
            source_id="source:demo_manual",
            title="Generalized demo source",
            kind="demo",
            permission="allowed",
            notes="Fictional source for OAK-safe demo.",
        )
    )

    evidence = EvidenceGraph()
    evidence.add(
        EvidenceItem(
            evidence_id="evidence:demo_bridge_review",
            claim="Demo bridge has a review maintenance signal.",
            source_id="source:demo_manual",
            asset_id="asset:demo_bridge",
            status="structured_evidence",
            confidence=0.7,
            method="demo_fixture",
            limitations="Fictional example; no real asset assessment.",
        )
    )

    risks = [
        InfraRiskTensor(
            risk_id="risk:demo_bridge",
            asset_id="asset:demo_bridge",
            physical_condition=3,
            service_criticality=3,
            public_dependency=3,
            climate_exposure=2,
            maintenance_debt=3,
            notes="Demo risk signal only.",
        ),
        InfraRiskTensor(
            risk_id="risk:demo_water_facility",
            asset_id="asset:demo_water_facility",
            service_criticality=4,
            public_dependency=5,
            privacy_security_sensitivity=3,
            maintenance_debt=2,
            notes="Review-only generalized signal.",
        ),
    ]

    maintenance = [
        MaintenanceSignal(
            signal_id="maint:demo_bridge",
            asset_id="asset:demo_bridge",
            condition_score=3,
            service_criticality=3,
            maintenance_debt=3,
            climate_exposure=2,
            cost_of_delay=3,
            evidence_quality=3,
            notes="Demo maintenance prioritization signal.",
        )
    ]

    scenarios = [
        ResilienceScenario(
            scenario_id="scenario:demo_ice_storm",
            name="Generalized ice storm scenario",
            kind="ice_storm",
            affected_asset_ids=["asset:demo_bridge", "asset:demo_school"],
            expected_service_impact=3,
            preparedness_level=3,
            recovery_complexity=2,
            evidence_quality=3,
            notes="Public-safe generalized scenario.",
        )
    ]

    gate = OAKSecurityGate().evaluate_publication_context(
        source_is_authorized=True,
        human_review_done=True,
        public_safe_redaction_done=True,
    )

    report = MarkdownReportFactory().render_system_report(
        title="InfrastructureGraph Quebec — Public-Safe Demo",
        graph=graph,
        sources=sources,
        evidence=evidence,
        risks=risks,
        maintenance=maintenance,
        scenarios=scenarios,
        security_gate=gate,
        public_safe=True,
    )

    bundle = InfraExportBundle(
        graph=graph,
        sources=sources,
        evidence=evidence,
        risks=risks,
        maintenance=maintenance,
        scenarios=scenarios,
        security_gate=gate,
        metadata={"demo": True, "real_assets": False},
    )

    return InfraDemoArtifacts(
        report_markdown=report.to_markdown(),
        bundle_json=JsonExporter().export_bundle(bundle, public_safe=True),
        metadata={"asset_count": graph.quality_report()["asset_count"], "security_status": gate.status},
    )
