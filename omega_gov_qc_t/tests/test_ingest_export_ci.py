from omega_gov_qc_t import (
    DatasetHealthEngine,
    ExportBundle,
    GovGraph,
    GovNode,
    JsonExporter,
    OpenDataIngestor,
    SourceRecord,
    SourceRegistry,
)


def _allowed_source():
    return SourceRecord(
        source_id="source:demo_open_data",
        title="Demo Open Data",
        kind="example",
        locator="example://open-data-demo",
        permission="allowed",
    )


def test_csv_ingestion_and_dataset_health():
    csv_text = "id,name,type\n1,Alpha,service\n2,Beta,dataset\n3,,municipality\n"
    result = OpenDataIngestor().from_csv_text(
        dataset_id="dataset:csv_demo",
        title="CSV Demo",
        source=_allowed_source(),
        csv_text=csv_text,
    )

    assert result.dataset.row_count == 3
    assert result.dataset.field_count == 3
    assert result.warnings == []

    health = DatasetHealthEngine().evaluate(result.dataset)
    assert health.oak_ready is True
    assert health.missing_cell_count == 1


def test_json_ingestion_and_dataset_health():
    json_text = '{"records":[{"id":"1","name":"Alpha"},{"id":"2","name":null}]}'
    result = OpenDataIngestor().from_json_text(
        dataset_id="dataset:json_demo",
        title="JSON Demo",
        source=_allowed_source(),
        json_text=json_text,
    )

    assert result.dataset.row_count == 2
    assert set(result.dataset.fields) == {"id", "name"}

    health = DatasetHealthEngine().evaluate(result.dataset)
    assert health.missing_cell_count == 1
    assert health.band in {"good", "review"}


def test_ingestor_warns_when_source_needs_review():
    source = SourceRecord(
        source_id="source:review",
        title="Review Source",
        kind="example",
        locator="example://review",
        permission="review_required",
    )
    result = OpenDataIngestor().from_csv_text(
        dataset_id="dataset:review",
        title="Review Dataset",
        source=source,
        csv_text="id\n1\n",
    )

    assert "source_permission_not_allowed" in result.warnings


def test_json_export_bundle_is_deterministic_and_contains_oak_note():
    graph = GovGraph()
    graph.add_node(
        GovNode(
            node_id="dataset:demo",
            name="Demo Dataset",
            node_type="dataset",
            source="source:demo_open_data",
        )
    )
    sources = SourceRegistry()
    sources.add(_allowed_source())

    bundle = ExportBundle(
        name="demo_bundle",
        graph=graph,
        sources=sources,
        metadata={"purpose": "test"},
    )
    text = JsonExporter().export_bundle(bundle)

    assert "demo_bundle" in text
    assert "oak_note" in text
    assert text.endswith("\n")
