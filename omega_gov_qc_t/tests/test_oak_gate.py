from omega_gov_qc_t import GovEdge, GovGraph, GovNode, OAKGate


def test_open_data_mapping_is_deployable_when_low_risk():
    report = OAKGate().evaluate_context(
        use_case="open_data_mapping",
        contains_personal_data=False,
        makes_sensitive_decision=False,
        source_is_authorized=True,
        human_review_required=False,
    )

    assert report.deployable is True
    assert not report.failures()


def test_high_impact_context_requires_human_authority_and_review():
    report = OAKGate().evaluate_context(
        use_case="high_impact_public_context",
        contains_personal_data=True,
        makes_sensitive_decision=True,
        source_is_authorized=True,
        human_review_required=False,
        domain="health",
        fairness_review_done=False,
    )

    assert report.deployable is False
    failure_names = {failure.name for failure in report.failures()}
    assert "HumanAuthorityGate" in failure_names
    assert "PrivacyGate" in failure_names
    assert "FairnessGate" in failure_names


def test_gov_graph_quality_report_tracks_isolates():
    graph = GovGraph()
    graph.add_node(
        GovNode(
            node_id="jurisdiction:quebec",
            name="Quebec",
            node_type="region",
            source="test",
        )
    )
    graph.add_node(
        GovNode(
            node_id="module:opendata_cvcd",
            name="OPEN-DATA-CVCD",
            node_type="dataset",
            source="test",
        )
    )
    graph.add_edge(
        GovEdge(
            source_id="jurisdiction:quebec",
            target_id="module:opendata_cvcd",
            relation="contains_candidate_system",
            evidence="test",
        )
    )

    quality = graph.quality_report()
    assert quality["node_count"] == 2
    assert quality["edge_count"] == 1
    assert quality["isolated_nodes"] == []
