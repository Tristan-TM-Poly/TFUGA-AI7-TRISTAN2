import json
from pathlib import Path

from omega_gov_qc_t import MunicipalReportBuilder, OAKIssueBundleMapper, label_names
from omega_gov_qc_t.cli import main


def test_bundle_mapper_generates_v09_issue_bundle():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueBundleMapper().from_json_text(artifacts.bundle_json)

    assert bundle.schema == "omega_gov_qc_t.oak_issue_bundle.v0.9"
    assert bundle.source_bundle == "municipal_demo_bundle"
    assert len(bundle.issues) == 4
    assert all("bundle-review" in issue.labels for issue in bundle.issues)


def test_bundle_mapper_rejects_unknown_schema():
    payload = json.dumps({"schema": "unknown", "name": "bad"})

    try:
        OAKIssueBundleMapper().from_json_text(payload)
    except ValueError as exc:
        assert "unsupported export bundle schema" in str(exc)
    else:
        raise AssertionError("unsupported schema should raise ValueError")


def test_cli_issues_from_bundle_outputs_json_and_markdown(tmp_path: Path):
    bundle_path = tmp_path / "bundle.json"
    json_path = tmp_path / "issues_from_bundle.json"
    md_path = tmp_path / "issues_from_bundle.md"

    assert main(["bundle", "--out", str(bundle_path)]) == 0
    assert main(["issues-from-bundle-json", "--bundle", str(bundle_path), "--out", str(json_path)]) == 0
    assert main(["issues-from-bundle-md", "--bundle", str(bundle_path), "--out", str(md_path)]) == 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["schema"] == "omega_gov_qc_t.oak_issue_bundle.v0.9"
    assert "local bundle" in markdown.lower()
    assert "Risk entries" in markdown


def test_label_manifest_cli_and_exports(tmp_path: Path):
    label_path = tmp_path / "labels.json"

    assert "omega-gov-qc" in label_names()
    assert "bundle-review" in label_names()
    assert main(["labels-json", "--out", str(label_path)]) == 0

    labels = json.loads(label_path.read_text(encoding="utf-8"))
    assert "omega-gov-qc" in labels
    assert "bundle-review" in labels


def test_cli_demo_includes_label_manifest(tmp_path: Path):
    out_dir = tmp_path / "demo"

    assert main(["demo", "--out", str(out_dir)]) == 0
    assert (out_dir / "oak_issue_labels.json").exists()
