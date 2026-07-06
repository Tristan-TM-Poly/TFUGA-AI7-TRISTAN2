import json

from omega_infra_qc_t import JsonExporter, build_demo_artifacts
from omega_infra_qc_t.cli import main


def test_demo_builder_returns_report_and_bundle():
    artifacts = build_demo_artifacts()

    assert "InfrastructureGraph Quebec" in artifacts.report_markdown
    assert artifacts.metadata["asset_count"] == 3
    payload = json.loads(artifacts.bundle_json)
    assert payload["schema"] == "omega_infra_qc_t.export_bundle.v0"
    assert payload["public_safe"] is True
    assert payload["security_gate"]["status"] == "pass"


def test_json_exporter_is_deterministic_for_same_payload():
    payload = {"b": 2, "a": 1}
    first = JsonExporter.canonical_json(payload)
    second = JsonExporter.canonical_json(payload)

    assert first == second
    assert first.splitlines()[1].startswith('  "a"')


def test_cli_demo_writes_report_and_bundle(tmp_path):
    out_dir = tmp_path / "demo"

    exit_code = main(["demo", "--out", str(out_dir)])

    assert exit_code == 0
    assert (out_dir / "infra_qc_demo_report.md").exists()
    assert (out_dir / "infra_qc_demo_bundle.json").exists()


def test_cli_individual_outputs(tmp_path):
    report_path = tmp_path / "report.md"
    bundle_path = tmp_path / "bundle.json"

    assert main(["report", "--out", str(report_path)]) == 0
    assert main(["bundle", "--out", str(bundle_path)]) == 0

    assert "Security Gate" in report_path.read_text(encoding="utf-8")
    assert json.loads(bundle_path.read_text(encoding="utf-8"))["schema"] == "omega_infra_qc_t.export_bundle.v0"
