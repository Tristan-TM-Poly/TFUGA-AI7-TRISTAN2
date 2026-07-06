import json
from pathlib import Path

from omega_gov_qc_t import MunicipalReportBuilder, OAKIssueGenerator
from omega_gov_qc_t.cli import main


def test_oak_issue_generator_creates_review_safe_drafts():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueGenerator().from_demo_artifacts(artifacts)

    assert bundle.schema == "omega_gov_qc_t.oak_issue_bundle.v0.8"
    assert len(bundle.issues) >= 4
    assert "not accusations" in bundle.to_markdown().lower()
    assert "fraud" in bundle.disclaimer.lower()
    assert all(issue.oak_status for issue in bundle.issues)
    assert all("omega-gov-qc" in issue.labels for issue in bundle.issues)


def test_oak_issue_bundle_json_is_deterministic_shape():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueGenerator().from_demo_artifacts(artifacts)
    payload = json.loads(bundle.to_json())

    assert payload["schema"] == "omega_gov_qc_t.oak_issue_bundle.v0.8"
    assert payload["source_bundle"] == "municipal_demo_bundle"
    assert payload["issues"][0]["issue_id"] == "oak-issue:source-authorization-before-pilot"
    assert payload["issues"][1]["issue_type"] == "dataset_health"


def test_oak_issue_drafts_keep_non_accusation_boundary():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueGenerator().from_demo_artifacts(artifacts)
    markdown = bundle.to_markdown().lower()

    assert "not accusations" in markdown
    assert "not evidence of wrongdoing" in markdown
    assert "must not be used as final public-sector judgments" in markdown
    assert "review signal" in markdown


def test_cli_issue_outputs(tmp_path: Path):
    json_path = tmp_path / "issues.json"
    md_path = tmp_path / "issues.md"

    assert main(["issues-json", "--out", str(json_path)]) == 0
    assert main(["issues-md", "--out", str(md_path)]) == 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["schema"] == "omega_gov_qc_t.oak_issue_bundle.v0.8"
    assert "OAK Issue Drafts" in markdown
    assert "Human review" in markdown or "human-review" in markdown


def test_cli_demo_includes_issue_artifacts(tmp_path: Path):
    out_dir = tmp_path / "demo"

    assert main(["demo", "--out", str(out_dir)]) == 0
    assert (out_dir / "oak_issue_drafts.json").exists()
    assert (out_dir / "oak_issue_drafts.md").exists()
