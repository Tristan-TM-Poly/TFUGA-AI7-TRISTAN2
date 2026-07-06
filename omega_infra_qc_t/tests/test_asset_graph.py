from omega_infra_qc_t import AssetNode, DependencyEdge, InfraGraph


def test_asset_node_public_safe_summary_redacts_sensitive_asset():
    asset = AssetNode(
        asset_id="asset:restricted_demo",
        name="Restricted Demo Asset",
        sector="data",
        visibility="restricted",
        criticality=4,
        municipality="Sensitive Municipality",
        notes="Sensitive notes",
    )

    payload = asset.to_dict(public_safe=True)

    assert payload["name"] == "redacted_asset"
    assert payload["municipality"] == "redacted"
    assert payload["notes"] == "redacted"


def test_infra_graph_adds_assets_and_dependencies():
    graph = InfraGraph()
    graph.add_asset(AssetNode(asset_id="asset:a", name="A", sector="transport"))
    graph.add_asset(AssetNode(asset_id="asset:b", name="B", sector="water"))
    graph.add_dependency(DependencyEdge(source_asset_id="asset:a", target_asset_id="asset:b", kind="depends_on"))

    quality = graph.quality_report()

    assert quality["asset_count"] == 2
    assert quality["dependency_count"] == 1
    assert quality["sectors"]["transport"] == 1


def test_infra_graph_rejects_unknown_dependency_target():
    graph = InfraGraph()
    graph.add_asset(AssetNode(asset_id="asset:a", name="A"))

    try:
        graph.add_dependency(DependencyEdge(source_asset_id="asset:a", target_asset_id="asset:missing"))
    except ValueError as exc:
        assert "unknown target asset" in str(exc)
    else:
        raise AssertionError("expected ValueError")
