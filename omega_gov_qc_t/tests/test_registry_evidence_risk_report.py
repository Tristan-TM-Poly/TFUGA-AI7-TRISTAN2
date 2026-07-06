from omega_gov_qc_t import (
    EvidenceGraph,
    EvidenceItem,
    GovEdge,
    GovGraph,
    GovNode,
    MarkdownReportFactory,
    OAKGate,
    RiskRegister,
    RiskTensor,
    SourceRecord,
    SourceRegistry,
)


def test_source_registry_records_fingerprint():
    registry = SourceRegistry()
    registry.add(
        SourceRecord(
            source_id="source:demo",
            title="Demo public source",
            kind="example",
            locator="example://demo",
            permission="allowed",
        )
    )

    exported = registry.to_dict()
    assert exported["quality_report"]["source_count"] == 1
    assert len(exported["sources"][0]["fingerprint"]) == 64


def test_evidence_graph_rejects_human_decision_generation():
    graph = EvidenceGraph()
    item = EvidenceItem(
        evidence_id="evidence:demo",
        claim="Demo claim for review",
        source_id="source:demo",
        status="human_decision",
    )

    try:
        graph.add(item)
    except ValueError as exc:
        assert "human_decision" in str(exc)
    else:
        raise AssertionError("human_decision evidence should be rejected")


def test_risk_tensor_blocks_high_privacy_context():
    risk = RiskTensor(
        risk_id="risk:demo",
        name="Demo high privacy context",
        privacy=4,
        public_utility=4,
        evidence_quality=3,
        reversibility=3,
    )

    assert risk.blocks_deployment is True
    assert risk.band in {"medium", "high", "critical"}


def test_markdown_report_factory_renders_sections():
    gov_graph = GovGraph()
    gov_graph.add_node(
        GovNode(
            node_id="municipality:demo",
            name="Demo Municipality",
            node_type="municipality",
            source="source:demo",
        )
    )
    gov_graph.add_node(
        GovNode(
            node_id="service:demo",
            name="Demo Public Service",
            node_type="service",
            source="source:demo",
        )
    )
    gov_graph.add_edge(
        GovEdge(
            source_id="municipality:demo",
            target_id="service:demo",
            relation="offers",
            evidence="source:demo",
        )
    )

    sources = SourceRegistry()
    sources.add(
        SourceRecord(
            source_id="source:demo",
            title="Demo source",
            kind="example",
            locator="example://demo",
            permission="allowed",
        )
    )

    evidence = EvidenceGraph()
    evidence.add(
        EvidenceItem(
            evidence_id="evidence:demo",
            claim="Demo service exists in placeholder graph",
            source_id="source:demo",
            limitations="Example data only.",
        )
    )

    risks = RiskRegister()
    risks.add(
        RiskTensor(
            risk_id="risk:demo",
            name="Example risk",
            legal=0,
            privacy=0,
            security=0,
            fairness=0,
            human_impact=0,
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
        title="Municipality demo",
        graph=gov_graph,
        sources=sources,
        evidence=evidence,
        risks=risks,
        oak_report=oak_report,
        recommendations=["Keep this as example-only until source policy is reviewed."],
    )

    text = report.to_markdown()
    assert "# Municipality demo" in text
    assert "## 5. OAKGate" in text
    assert "Deployable: True" in text
