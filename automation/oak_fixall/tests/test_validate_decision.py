import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "automation" / "oak_fixall"))

from validate_decision import validate_decision  # noqa: E402


def base_decision():
    return {
        "repo": "Tristan-TM-Poly/example",
        "item_type": "pull_request",
        "item_id": "1",
        "observed_state": {
            "open": True,
            "draft": False,
            "mergeable": True,
            "checks_state": "green",
            "external_status_state": "absent",
            "scope_coherent": True,
            "sensitive_risk": "none",
        },
        "blockers": [],
        "decision": "MERGE_NOW",
        "oak_constraints": {
            "non_destructive": True,
            "no_secret_exposure": True,
            "no_bypass": True,
            "human_sensitive_safe": True,
        },
        "next_action": "Merge with head SHA lock.",
    }


def test_clean_merge_now_passes():
    assert validate_decision(base_decision()) == []


def test_draft_cannot_merge_now():
    data = base_decision()
    data["observed_state"]["draft"] = True
    errors = validate_decision(data)
    assert any("draft" in error for error in errors)


def test_non_mergeable_cannot_merge_now():
    data = base_decision()
    data["observed_state"]["mergeable"] = False
    errors = validate_decision(data)
    assert any("MERGE_NOW requires mergeable" in error or "non-mergeable" in error for error in errors)


def test_merge_now_requires_empty_blockers():
    data = base_decision()
    data["blockers"] = ["CI_RED"]
    errors = validate_decision(data)
    assert any("empty blocker" in error for error in errors)


def test_oak_constraints_must_be_true():
    data = base_decision()
    data["oak_constraints"]["no_bypass"] = False
    errors = validate_decision(data)
    assert any("no_bypass" in error for error in errors)


def test_existing_example_json_is_valid_shape():
    example = ROOT / "automation" / "oak_fixall" / "examples" / "hyperatlas_safe_extraction.decision.json"
    if example.exists():
        data = json.loads(example.read_text(encoding="utf-8"))
        errors = validate_decision(data)
        assert not [error for error in errors if error.startswith("missing required")]
