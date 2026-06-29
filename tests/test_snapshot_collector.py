from __future__ import annotations

import json
from pathlib import Path

from tools.action_dashboard.snapshot_collector import collect_snapshot, write_snapshot


def make_repo(root: Path) -> None:
    (root / "README.md").write_text("repo", encoding="utf-8")
    (root / "demo_packets" / "datacenter_energy_oak").mkdir(parents=True)
    (root / "demo_packets" / "datacenter_energy_oak" / "README.md").write_text("ready", encoding="utf-8")
    (root / "demo_packets" / "paper_to_code_oak").mkdir(parents=True)
    (root / "demo_packets" / "paper_to_code_oak" / "README.md").write_text("status: seed_packet", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "OMEGA_ACTION_DASHBOARD_T.md").write_text("OAK", encoding="utf-8")
    (root / "orchestration").mkdir()
    (root / "orchestration" / "dashboard_ci_manifest.yaml").write_text("status: active", encoding="utf-8")
    (root / "tools" / "action_dashboard").mkdir(parents=True)
    (root / "tools" / "action_dashboard" / "dashboard_report_generator.py").write_text("# generator", encoding="utf-8")
    (root / "tools" / "action_dashboard" / "snapshot_collector.py").write_text("# collector", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_dashboard_report_generator.py").write_text("def test_x(): pass", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "action-dashboard-ci.yml").write_text("name: ci", encoding="utf-8")
    (root / "university_outreach" / "quebec_universities").mkdir(parents=True)
    (root / "university_outreach" / "quebec_universities" / "routes.yaml").write_text(
        "GREEN_EMAIL\nGREEN_FORM\nYELLOW_RESEARCH\n", encoding="utf-8"
    )


def test_collect_snapshot_counts_core_assets(tmp_path: Path) -> None:
    make_repo(tmp_path)
    snapshot = collect_snapshot(tmp_path)

    assert snapshot["dashboard_id"] == "omega-action-dashboard-local-snapshot"
    assert snapshot["lanes"]["proof_packets"]["ready_packets"] == 2
    assert snapshot["lanes"]["proof_packets"]["seed_packets"] == 1
    assert snapshot["lanes"]["github"]["workflow_files"] == 1
    assert snapshot["lanes"]["github"]["test_files"] == 1
    assert snapshot["lanes"]["universities"]["GREEN_EMAIL"] == 1
    assert snapshot["external_action_governor"]["internal_auto"] == ["collect_snapshot"]


def test_write_snapshot_outputs_json(tmp_path: Path) -> None:
    make_repo(tmp_path)
    output = tmp_path / "snapshot.json"

    snapshot = write_snapshot(tmp_path, output)
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert output.exists()
    assert loaded["dashboard_id"] == snapshot["dashboard_id"]
    assert loaded["safe_actions"] == ["collect_snapshot"]
