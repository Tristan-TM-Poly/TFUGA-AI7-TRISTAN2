import json
from pathlib import Path

from omega_gov_qc_t import (
    MunicipalReportBuilder,
    OAKIssueBundleMapper,
    OAKIssueSeverityPolicy,
    OAKSeverityReportBuilder,
    severity_json,
)
from omega_gov_qc_t.cli import main


def test_dataset_health_severity_blocks_unreadable_dataset():
    decision = OAKIssueSeverityPolicy().dataset_health(
        {
            "band": "blocked",
            "missing_ratio": 1.0,
            "duplicate_ratio": 0.0,
            "machine_readable": False,
        }
    )

    assert decision.priority == "P0"
    assert decision.status == "blocked_until_dataset_review"
    assert "dataset_not_machine_readable" in decision.reasons


def test_dataset_health_severity_for_review_band_is_p2():
    decision = OAKIssueSeverityPolicy().dataset_health(
        {
            "band": "review",
            "missing_ratio": 0.1,
            "duplicate_ratio": 0.0,
            "machine_readable": True,
        }
    )

    assert decision.priority == "P2"
    assert decision.status == "review_recommended"
    assert "final finding" in decision.oak_note


def test_risk_register_severity_uses_exported_risk_fields():
    decision = OAKIssueSeverityPolicy().risk_register(
        {
            "risks": [
                {
                    "legal": 5,
                    "privacy": 5,
                    "security": 5,
                    "fairness": 5,
                    "human_impact": 1,
                    "reversibility": 1,
                    "evidence_quality": 1,
                    "public_utility": 1,
                    "risk_pressure": 21,
                    "band": "critical",
                    "blocks_deployment": True,
                }
            ],
            "quality_report": {"blockers": ["risk:example"]},
        }
    )

    assert decision.priority == "P0"
    assert decision.status == "blocked_until_risk_review"
    assert "quality_report_contains_blockers" in decision.reasons
    assert "risk_register_contains_critical_band" in decision.reasons


def test_severity_json_shape_is_stable():
    decision = OAKIssueSeverityPolicy().dataset_health({"band": "good", "missing_ratio": 0.0})
    payload = json.loads(severity_json(decision))

    assert sorted(payload.keys()) == ["oak_note", "priority", "reasons", "status"]
    assert payload["priority"] == "P3"


def test_bundle_mapper_v1_schema_and_severity_markdown():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueBundleMapper().from_json_text(artifacts.bundle_json)
    markdown = bundle.to_markdown()

    assert bundle.schema == "omega_gov_qc_t.oak_issue_bundle.v1.0"
    assert "## Local severity" in markdown
    assert "Severity is a workflow triage signal" in markdown
    assert any(issue.priority in {"P0", "P1", "P2", "P3"} for issue in bundle.issues)


def test_bundle_mapper_markdown_snapshot_core_sections():
    artifacts = MunicipalReportBuilder().build_demo()
    bundle = OAKIssueBundleMapper().from_json_text(artifacts.bundle_json)
    markdown = bundle.to_markdown()

    expected_sections = [
        "# Ω-GOV-QC-T OAK Issue Drafts",
        "## OAK review: verify source registry for local bundle",
        "## OAK review: validate dataset health signals for local bundle",
        "## OAK review: check graph and evidence semantics for local bundle",
        "## OAK review: inspect risk register before operational use",
        "## Disclaimer",
    ]
    for section in expected_sections:
        assert section in markdown


def test_aggregate_severity_report_json_and_markdown():
    artifacts = MunicipalReportBuilder().build_demo()
    report = OAKSeverityReportBuilder().from_json_text(artifacts.bundle_json)

    payload = json.loads(report.to_json())
    markdown = report.to_markdown()

    assert payload["schema"] == "omega_gov_qc_t.oak_severity_report.v1.0"
    assert payload["overall_priority"] in {"P0", "P1", "P2", "P3"}
    assert "source_registry" in payload["decisions"]
    assert "# Ω-GOV-QC-T OAK Severity Report" in markdown
    assert "## Decisions" in markdown


def test_cli_severity_outputs_and_demo_artifacts(tmp_path: Path):
    bundle_path = tmp_path / "bundle.json"
    json_path = tmp_path / "severity.json"
    md_path = tmp_path / "severity.md"
    demo_dir = tmp_path / "demo"

    assert main(["bundle", "--out", str(bundle_path)]) == 0
    assert main(["severity-json", "--bundle", str(bundle_path), "--out", str(json_path)]) == 0
    assert main(["severity-md", "--bundle", str(bundle_path), "--out", str(md_path)]) == 0
    assert main(["demo", "--out", str(demo_dir)]) == 0

    assert "oak_severity_report.v1.0" in json_path.read_text(encoding="utf-8")
    assert "OAK Severity Report" in md_path.read_text(encoding="utf-8")
    assert (demo_dir / "oak_severity_report.json").exists()
    assert (demo_dir / "oak_severity_report.md").exists()
