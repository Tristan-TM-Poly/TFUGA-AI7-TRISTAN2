from __future__ import annotations

import json

from tools.action_dashboard.dashboard_report_generator import (
    normalize_dashboard,
    rank_next_best_actions,
    render_markdown,
    write_dashboard_report,
)


def sample_snapshot() -> dict:
    return {
        "dashboard_id": "test-dashboard",
        "generated_at": "2026-06-29T00:00:00Z",
        "next_best_actions": [
            {"action_id": "low", "lane": "github", "title": "Low", "score": 0.2, "decision": "WATCH", "expected_output": "later"},
            {"action_id": "high", "lane": "dashboard", "title": "High", "score": 0.9, "decision": "ACT", "expected_output": "report"},
        ],
        "top_blockers": [
            {"blocker_class": "pending_checks", "affected_lane": "github", "safest_next_action": "WAIT_COOLDOWN"}
        ],
        "lanes": {"github": {"open_PRs": 2, "merged_PRs": 1}},
        "proof_assets": ["packet"],
        "merged_PRs": ["PR 1"],
        "demo_packets": ["demo"],
        "official_routes": ["route"],
        "actions_attempted": ["a", "b"],
        "safe_actions": ["a", "b"],
        "loop_upgrades": ["upgrade"],
        "assets_created": ["asset"],
        "frictions_burned": ["friction"],
        "M_plus_new": ["success"],
        "M_minus_new": ["blocker"],
        "anti_repetition_rules_added": ["rule"],
        "external_action_governor": {"internal_auto": ["report"], "blocked_until_approval": []},
    }


def test_rank_next_best_actions_descending() -> None:
    ranked = rank_next_best_actions(sample_snapshot()["next_best_actions"])
    assert [action["action_id"] for action in ranked] == ["high", "low"]


def test_normalize_dashboard_computes_metrics() -> None:
    report = normalize_dashboard(sample_snapshot())
    assert report["metrics"]["proof_capital"] > 0
    assert report["metrics"]["OAK_safety_ratio"] == 1.0
    assert report["executive_state"]["next_best_actions"][0]["action_id"] == "high"


def test_render_markdown_contains_core_sections() -> None:
    markdown = render_markdown(normalize_dashboard(sample_snapshot()))
    assert "Ω Action Dashboard Report" in markdown
    assert "Next Best Actions" in markdown
    assert "High" in markdown
    assert "pending_checks" in markdown


def test_write_dashboard_report_outputs_files(tmp_path) -> None:
    snapshot_path = tmp_path / "snapshot.json"
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    snapshot_path.write_text(json.dumps(sample_snapshot()), encoding="utf-8")

    report = write_dashboard_report(snapshot_path, markdown_path, json_path)

    assert report["dashboard_id"] == "test-dashboard"
    assert markdown_path.exists()
    assert json_path.exists()
    assert "Ω Action Dashboard Report" in markdown_path.read_text(encoding="utf-8")
