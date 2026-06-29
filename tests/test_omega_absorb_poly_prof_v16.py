import json
from pathlib import Path

from omega_prof_poly_t import (
    VERSION,
    apply_source_oak_policy,
    build_github_work_bundle,
    compile_top_next_actions,
    detect_source_family,
    route_records,
    run_cli,
    run_ingest_json_pipeline_v2,
    select_demo_records,
    write_action_packets,
    write_github_work_bundle,
)
from omega_prof_poly_t.poly_research_twin_v2 import build_poly_research_twin_v2


def test_v16_cli_commands(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps([{"id": "x", "title": "Local Demo", "authors": ["A"]}]), encoding="utf-8")
    assert VERSION
    assert run_cli(["version"]).startswith("omega-absorb ")
    assert run_cli(["route-source", "--input", str(path)]).startswith("source_id=")
    assert run_cli(["policy-check", "--input", str(path)]).startswith("status=")
    assert run_cli(["ingest-json-v2", "--input", str(path)]).startswith("route=")


def test_adapter_router_and_policy():
    route = detect_source_family({"dc.title": "Paper", "dc.creator": ["A"]})
    assert route.source_id == "polypublie"
    routed = route_records(select_demo_records("combined"))
    assert routed.normalized_records
    policy = apply_source_oak_policy(routed.records, routed.route.source_id)
    assert policy.status in {"allow", "allow_with_warnings", "blocked"}


def test_ingest_json_pipeline_v2(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps([{"id": "x", "title": "Local Demo", "authors": ["A"], "claims": ["C"], "methods": ["M"]}]), encoding="utf-8")
    result = run_ingest_json_pipeline_v2(path, "generic")
    assert result.atom_count == 1
    assert result.action_count > 0
    assert "entries" in result.manifest_json


def test_action_packet_writer(tmp_path: Path):
    twin = build_poly_research_twin_v2(select_demo_records("combined"))
    actions = compile_top_next_actions(twin)
    result = write_action_packets(actions.actions, tmp_path / "actions")
    assert result.files
    assert Path(result.manifest_path).exists()


def test_github_work_bundle_writer(tmp_path: Path):
    twin = build_poly_research_twin_v2(select_demo_records("combined"))
    actions = compile_top_next_actions(twin)
    bundle = build_github_work_bundle(actions.actions)
    files = write_github_work_bundle(bundle, tmp_path / "github_bundle")
    assert bundle.packets
    assert len(files) >= 2
    assert any(path.endswith("branch_manifest.json") for path in files)


def test_new_cli_writers(tmp_path: Path):
    assert run_cli(["write-actions", "--output-dir", str(tmp_path / "actions")]).startswith("action_files=")
    assert run_cli(["github-bundle", "--output-dir", str(tmp_path / "gh")]).startswith("github_bundle_files=")
