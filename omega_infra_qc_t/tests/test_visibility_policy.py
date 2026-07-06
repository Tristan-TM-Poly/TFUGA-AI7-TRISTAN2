from omega_infra_qc_t import AssetNode, DependencyEdge, InfraGraph, GraphMLExporter


def test_public_safe_asset_export_redacts_review_restricted_and_critical_assets():
    for visibility in ["review", "restricted", "critical"]:
        asset = AssetNode(
            asset_id=f"asset:{visibility}",
            name=f"Sensitive {visibility}",
            sector="data",
            visibility=visibility,
            municipality="Sensitive Municipality",
            notes="Sensitive note",
        )
        payload = asset.to_dict(public_safe=True)
        assert payload["name"] == "redacted_asset"
        assert payload["municipality"] == "redacted"
        assert payload["notes"] == "redacted"


def test_public_safe_graphml_does_not_emit_sensitive_asset_names_or_notes():
    graph = InfraGraph()
    graph.add_asset(AssetNode(asset_id="asset:public", name="Public Demo", visibility="public"))
    graph.add_asset(
        AssetNode(
            asset_id="asset:restricted",
            name="Restricted Demo Name",
            visibility="restricted",
            criticality=4,
            notes="Sensitive note should not appear.",
        )
    )
    graph.add_dependency(
        DependencyEdge(
            source_asset_id="asset:public",
            target_asset_id="asset:restricted",
            visibility="restricted",
            notes="Sensitive dependency note should not appear.",
        )
    )

    graphml = GraphMLExporter().export(graph, public_safe=True)

    assert "Public Demo" in graphml
    assert "Restricted Demo Name" not in graphml
    assert "Sensitive note" not in graphml
    assert "Sensitive dependency" not in graphml
    assert "redacted_asset" in graphml


def test_full_graphml_can_emit_private_labels_only_when_not_public_safe():
    graph = InfraGraph()
    graph.add_asset(AssetNode(asset_id="asset:restricted", name="Restricted Demo Name", visibility="restricted"))

    graphml = GraphMLExporter().export(graph, public_safe=False)

    assert "Restricted Demo Name" in graphml
