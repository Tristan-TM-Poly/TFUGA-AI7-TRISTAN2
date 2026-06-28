import json
from pathlib import Path

from omega_prof_poly_t import (
    VERSION,
    build_export_bundle,
    build_package_health_report,
    generate_changelog,
    load_and_normalize_local_json,
    render_compact_table,
    run_cli,
    select_demo_records,
)
from omega_prof_poly_t.absorb_public_research import absorb_public_records
from omega_prof_poly_t.opportunity_ranker import rank_opportunity_bundles
from omega_prof_poly_t.research_opportunity_compiler import compile_research_opportunities


def test_v13_version_and_new_cli_commands():
    assert VERSION == "1.3.0"
    assert run_cli(["version"]) == "omega-absorb 1.3.0\n"
    assert run_cli(["health"]).startswith("# Omega Absorb Health")
    assert run_cli(["changelog"]).startswith("# Omega Absorb Changelog")


def test_local_json_loader_normalizes_records(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps([{"id": "x", "title": "Local Demo", "authors": ["A"]}]), encoding="utf-8")
    result = load_and_normalize_local_json(path, "generic")
    assert result.path == str(path)
    assert len(result.records) == 1
    assert result.normalized_records[0]["atom_id"] == "x"


def test_cli_ingest_json_outputs_validation_table(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps([{"id": "x", "title": "Local Demo"}]), encoding="utf-8")
    output = run_cli(["ingest-json", "--input", str(path)])
    assert output.startswith("level | record_id")


def test_compact_table_renders_ranking():
    absorption = absorb_public_records(select_demo_records("combined"))
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    table = render_compact_table(ranking)
    assert table.startswith("rank | atom_id")
    assert "generate_ranked_backlog_item" in table


def test_export_bundle_writes_files(tmp_path: Path):
    result = build_export_bundle("combined", tmp_path / "bundle")
    assert len(result.files) >= 8
    assert (tmp_path / "bundle" / "manifest.json").exists()
    assert "bundle_version" in result.manifest_json


def test_package_health_and_changelog():
    health = build_package_health_report()
    assert health.version == "1.3.0"
    assert health.score > 0
    changelog = generate_changelog()
    assert "## v1.3" in changelog
