import json

from omega_gov_qc_t import MunicipalReportBuilder, OAKIssueBundleMapper, OAKIssueSeverityPolicy, severity_json


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


def test_risk_register_severity_uses_local_priority_only():
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
                }
            ]
        }
    )

    assert decision.priority == "P1"
    assert decision.status == "risk_review_required"
    assert "risk_register_contains_high_impact_items" in decision.reasons


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
