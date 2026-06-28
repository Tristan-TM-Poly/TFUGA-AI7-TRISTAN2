from pathlib import Path

from omega_prof_poly_t import (
    VERSION,
    build_documentation_index,
    build_export_payloads,
    render_documentation_index,
    run_cli,
    write_release_bundle,
)


def test_cli_reports_a_version():
    assert VERSION
    assert run_cli(["version"]).startswith("omega-absorb ")


def test_cli_json_exports():
    assert "artifact_count" in run_cli(["summary-json"])
    assert "valid_count" in run_cli(["validation-json"])
    assert "nodes" in run_cli(["graph-json"])


def test_export_payloads_are_nonempty():
    payloads = build_export_payloads()
    assert payloads.summary_json
    assert payloads.validation_json
    assert payloads.graph_json
    assert payloads.next_action == "write_selected_payload"


def test_write_release_bundle_uses_target_directory(tmp_path: Path):
    result = write_release_bundle(tmp_path / "bundle")
    assert len(result.files) == 3
    assert all(Path(item.path).exists() for item in result.files)
    assert result.next_action == "bundle_files_written"


def test_documentation_index_renders_versions():
    index = build_documentation_index()
    text = render_documentation_index()
    assert index.entries
    assert "ABSORB_POLY_PROF_V1_1.md" in text
