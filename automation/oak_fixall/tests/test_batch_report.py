import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "automation" / "oak_fixall"))

from batch_report import load_decision, render_markdown, summarize  # noqa: E402


def decision(item_id, decision, blockers=None):
    return {
        "repo": "Tristan-TM-Poly/example",
        "item_type": "pull_request",
        "item_id": str(item_id),
        "observed_state": {
            "open": True,
            "draft": False,
            "mergeable": decision == "MERGE_NOW",
            "checks_state": "green" if decision == "MERGE_NOW" else "red",
            "external_status_state": "absent",
            "scope_coherent": True,
            "sensitive_risk": "none",
        },
        "blockers": blockers or [],
        "decision": decision,
        "oak_constraints": {
            "non_destructive": True,
            "no_secret_exposure": True,
            "no_bypass": True,
            "human_sensitive_safe": True,
        },
        "next_action": "dry run only",
        "_errors": [],
        "_path": f"{item_id}.json",
    }


def test_summarize_counts_decisions_and_blockers():
    items = [
        decision(1, "MERGE_NOW"),
        decision(2, "BLOCK_M_MINUS", ["CI_RED", "SCOPE_MISMATCH"]),
        decision(3, "BLOCK_M_MINUS", ["CI_RED"]),
    ]
    summary = summarize(items)
    assert summary["total_items"] == 3
    assert summary["decision_counts"]["MERGE_NOW"] == 1
    assert summary["decision_counts"]["BLOCK_M_MINUS"] == 2
    assert summary["blocker_counts"]["CI_RED"] == 2
    assert summary["blocker_counts"]["SCOPE_MISMATCH"] == 1


def test_render_markdown_contains_oak_warning():
    items = [decision(1, "MERGE_NOW")]
    summary = summarize(items)
    markdown = render_markdown(summary, items)
    assert "Do not merge from this report alone" in markdown
    assert "MERGE_NOW" in markdown


def test_load_decision_attaches_validation_errors(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"decision": "MERGE_NOW"}), encoding="utf-8")
    data = load_decision(path)
    assert data["_errors"]
