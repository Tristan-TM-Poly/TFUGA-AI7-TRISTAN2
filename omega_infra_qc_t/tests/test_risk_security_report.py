from omega_infra_qc_t import (
    AssetNode,
    EvidenceGraph,
    EvidenceItem,
    InfraGraph,
    InfraRiskTensor,
    MaintenanceSignal,
    MarkdownReportFactory,
    OAKSecurityGate,
    ResilienceScenario,
    SourceRecord,
    SourceRegistry,
)


def test_risk_tensor_blocks_sensitive_publication():
    risk = InfraRiskTensor(
        risk_id="risk:critical",
        asset_id="asset:demo",
        service_criticality=5,
        privacy_security_sensitivity=4,
    )

    assert risk.band == "critical"
    assert risk.blocks_publication is True


def test_security_gate_blocks_sensitive_public_context():
    result = OAKSecurityGate().evaluate_publication_context(
        source_is_authorized=True,
        contains_exact_sensitive_location=True,
        human_review_done=True,
        public_safe_redaction_done=True,
    )

    assert result.status == "block"
    assert "exact_sensitive_location" in result.blockers
    assert result.publishable is False


def test_security_gate_passes_public_safe_reviewed_context():
    result = OAKSecurityGate().evaluate_publication_context(
        source_is_authorized=True,
        human_review_done=True,
        public_safe_redaction_done=True,
    )

    assert result.status == "pass"
    assert result.publishable is True


def test_maintenance_signal_priority_and_evidence_flag():
    signal = MaintenanceSignal(
        signal_id="maint:demo",
        asset_id="asset:demo_bridge",
        condition_score=4,
        service_criticality=3,
        maintenance_debt=4,
        climate_exposure=3,
        cost_of_delay=4,
        evidence_quality=2,
    )

    assert signal.band in {"priority", "urgent"}
    assert signal.needs_more_evidence is True


def test_report_factory_renders_markdown():
    graph = InfraGraph()
    graph.add_asset(AssetNode(asset_id="asset:demo_bridge", name="Demo Bridge", sector="transport"))

    sources = SourceRegistry()
    sources.add(SourceRecord(source_id="source:demo", title="Demo Source", permission="allowed"))

    evidence = EvidenceGraph()
    evidence.add(
        EvidenceItem(
            evidence_id="evidence:demo",
            claim="Demo bridge has a review signal.",
            source_id="source:demo",
            asset_id="asset:demo_bridge",
            status="structured_evidence",
        )
    )

    risk = InfraRiskTensor(risk_id="risk:demo", asset_id="asset:demo_bridge", physical_condition=2)
    maintenance = MaintenanceSignal(signal_id="maint:demo", asset_id="asset:demo_bridge", condition_score=2, evidence_quality=3)
    scenario = ResilienceScenario(
        scenario_id="scenario:demo",
        name="Demo Power Outage",
        kind="power_outage",
        affected_asset_ids=["asset:demo_bridge"],
        expected_service_impact=2,
        preparedness_level=3,
        recovery_complexity=2,
        evidence_quality=3,
    )
    gate = OAKSecurityGate().evaluate_publication_context(
        source_is_authorized=True,
        human_review_done=True,
        public_safe_redaction_done=True,
    )

    report = MarkdownReportFactory().render_system_report(
        title="Demo Infra Report",
        graph=graph,
        sources=sources,
        evidence=evidence,
        risks=[risk],
        maintenance=[maintenance],
        scenarios=[scenario],
        security_gate=gate,
    )

    text = report.to_markdown()
    assert "Demo Infra Report" in text
    assert "Security Gate" in text
    assert "Graph Summary" in text
    assert "Demo Power Outage" in text
