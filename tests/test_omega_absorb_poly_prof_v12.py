from pathlib import Path

from omega_prof_poly_t import (
    VERSION,
    available_demo_sources,
    build_export_payloads,
    build_package_status_report,
    run_cli,
    select_demo_records,
)


def test_v12_version_and_sources():
    assert VERSION == "1.2.0"
    assert run_cli(["version"]) == "omega-absorb 1.2.0\n"
    assert available_demo_sources() == ("combined", "polypublie", "expertise")
    assert "polypublie" in run_cli(["sources"])


def test_select_demo_records_by_source():
    assert len(select_demo_records("combined")) >= 2
    assert len(select_demo_records("polypublie")) == 1
    assert len(select_demo_records("expertise")) == 1


def test_cli_source_specific_json_and_graphml():
    assert "polypublie" in run_cli(["summary-json", "--source", "polypublie"])
    assert "expertise" in run_cli(["validation-json", "--source", "expertise"])
    assert "<graphml" in run_cli(["graphml", "--source", "combined"])


def test_docs_index_and_status_commands():
    assert run_cli(["docs-index"]).startswith("# Omega Absorb Documentation Index")
    assert run_cli(["status"]).startswith("# Omega Absorb Package Status")
    report = build_package_status_report()
    assert report.version == "1.2.0"
    assert "graphml" in report.cli_commands


def test_write_bundle_output_dir(tmp_path: Path):
    output = run_cli(["write-bundle", "--output-dir", str(tmp_path / "out")])
    assert "release_summary.json" in output
    assert (tmp_path / "out" / "release_summary.json").exists()


def test_export_payloads_include_graphml():
    payloads = build_export_payloads("combined")
    assert payloads.graphml.startswith("<?xml")
    assert payloads.source == "combined"
