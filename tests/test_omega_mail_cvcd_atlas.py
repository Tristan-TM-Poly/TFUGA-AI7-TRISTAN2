"""Structural and semantic checks for Ω-MAIL-T R0.2 CVCD materialization."""
from __future__ import annotations

from omega_mail_t.cvcd_atlas import (
    CVCDAtlas,
    EXPECTED_FILES_PER_LAYER,
    EXPECTED_RECORDS_PER_LAYER,
    EXPECTED_TOTAL_RECORDS,
    LAYERS,
    expected_cell_lines,
    parse_cell_line,
)


def test_canonical_cell_grid_has_64_unique_entries() -> None:
    lines = expected_cell_lines()
    assert len(lines) == 64
    assert len(set(lines)) == 64
    assert lines[0] == "a00|l0"
    assert lines[-1] == "a15|l3"
    assert all(parse_cell_line(line) for line in lines)


def test_materialized_atlas_has_49152_records() -> None:
    report = CVCDAtlas().audit()
    assert report.valid is True
    assert report.total_records == EXPECTED_TOTAL_RECORDS == 49_152
    assert report.expected_files == 768
    assert report.observed_files == 768
    assert report.unique_content_hashes == 1


def test_every_layer_has_16384_records() -> None:
    report = CVCDAtlas().audit()
    assert EXPECTED_FILES_PER_LAYER == 256
    assert EXPECTED_RECORDS_PER_LAYER == 16_384
    assert report.records_by_layer == {
        "oak": 16_384,
        "routing": 16_384,
        "scenario": 16_384,
    }


def test_specific_cell_decodes_all_semantic_coordinates() -> None:
    atlas = CVCDAtlas()
    cells = list(
        atlas.iter_cells(
            layer="oak",
            company="tristan_security",
            intent="security_alert",
            anomaly="permission_boundary",
            locale="fr-CA",
        )
    )
    assert len(cells) == 1
    cell = cells[0]
    assert cell.record_id == "mail:oak:c12:i02:a13:l0"
    assert cell.company == "tristan_security"
    assert cell.intent == "security_alert"
    assert cell.anomaly == "permission_boundary"
    assert cell.locale == "fr-CA"
    assert cell.synthetic is True
    assert cell.external_delivery_allowed is False


def test_each_scenario_has_routing_and_oak_companions() -> None:
    atlas = CVCDAtlas()
    selectors = {
        "company": "tristan_oak_systems",
        "intent": "invoice_dispute",
        "anomaly": "contradictory_identifier",
        "locale": "en-CA",
    }
    records = {
        layer: next(atlas.iter_cells(layer=layer, **selectors))
        for layer in LAYERS
    }
    suffixes = {
        record.record_id.split(":", maxsplit=2)[-1]
        for record in records.values()
    }
    assert len(suffixes) == 1
    assert set(records) == {"scenario", "routing", "oak"}


def test_manifest_refuses_external_delivery() -> None:
    atlas = CVCDAtlas()
    assert atlas.manifest["external_delivery_allowed"] is False
    assert atlas.manifest["data_classification"] == "synthetic_internal"
    assert atlas.audit().unsafe_manifest_flags == ()
