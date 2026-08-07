from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.dashboard import build_dashboard, write_dashboard
from omega_summary_fractal_t.identity import resolve_identity, write_identity_report
from omega_summary_fractal_t.index import append_snapshot
from omega_summary_fractal_t.query import query_payload, write_query


def _node(path: str, status: str, *, hashes=(), code=1, tests=0, workflows=0, documents=1, schemas=0):
    return {
        "id": f"system:{path}",
        "kind": "system",
        "path": path,
        "title": path,
        "one_line": f"System {path}",
        "status": status,
        "metrics": {
            "code_files": code,
            "tests": tests,
            "workflows": workflows,
            "documents": documents,
            "schemas": schemas,
            "implemented": bool(code),
            "tested": bool(code and tests),
            "documented": bool(documents),
            "schema_backed": bool(schemas),
        },
        "evidence": [
            {"path": f"artifact-{i}", "kind": "code", "status": "observed", "sha256": digest}
            for i, digest in enumerate(hashes)
        ],
    }


def _summary(nodes, *, fingerprint="fp"):
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-07T12:00:00Z",
        "root": "demo",
        "depth": 9,
        "audience": "oak",
        "focus": None,
        "nodes": nodes,
        "edges": [
            {"source": "system:omega_alpha_t", "target": "system:omega_beta_t", "relation": "DEPENDS_ON"}
        ] if any(node.get("path") == "omega_alpha_t" for node in nodes) and any(node.get("path") == "omega_beta_t" for node in nodes) else [],
        "health": {},
        "gaps": [],
        "duplicate_candidates": [],
        "cache_fingerprint": fingerprint,
    }


def test_identity_continuity_is_review_only_and_content_addressed(tmp_path: Path):
    previous = _summary([_node("omega_old_name_t", "tested", hashes=("a" * 64, "b" * 64), tests=1)])
    current = _summary([_node("omega_new_name_t", "tested", hashes=("a" * 64, "b" * 64), tests=1)], fingerprint="fp2")
    report = resolve_identity(previous, current)
    assert len(report["candidates"]) == 1
    candidate = report["candidates"][0]
    assert candidate["from"] == "omega_old_name_t"
    assert candidate["to"] == "omega_new_name_t"
    assert candidate["score"] == 1.0
    assert candidate["evidence"] == "exact_content_signature"
    assert candidate["one_to_one"] is True
    assert candidate["automatic_rewrite"] is False
    paths = write_identity_report(previous, current, tmp_path / "identity")
    assert paths["identity_json"].is_file()
    assert "review-only" in json.loads(paths["identity_json"].read_text())["boundary"]


def test_query_filters_status_relation_and_crystallization(tmp_path: Path):
    payload = _summary([
        _node("omega_alpha_t", "tested", tests=1, workflows=1, schemas=1),
        _node("omega_beta_t", "implemented"),
    ])
    report = query_payload(payload, kind="system", status="tested", relation="DEPENDS_ON", min_crystallization=0.8)
    assert report["total_matches"] == 1
    assert report["results"][0]["path"] == "omega_alpha_t"
    paths = write_query(report, tmp_path / "query")
    assert paths["query_json"].is_file()
    assert paths["query_markdown"].is_file()


def test_dashboard_separates_crystallization_and_proof_debt(tmp_path: Path):
    first = _summary([
        _node("omega_alpha_t", "implemented", tests=0, workflows=0, schemas=0),
        _node("omega_beta_t", "implemented", tests=0),
    ], fingerprint="fp1")
    second = _summary([
        _node("omega_alpha_t", "tested", tests=1, workflows=1, schemas=1),
        _node("omega_beta_t", "implemented", tests=0),
    ], fingerprint="fp2")
    index_path = tmp_path / "index.json"
    append_snapshot(index_path, first)
    append_snapshot(index_path, second)
    dashboard = build_dashboard(second, index=index_path)
    assert dashboard["systems"] == 2
    assert dashboard["status_counts"]["tested"] == 1
    assert dashboard["attention"]["implemented_without_tests"] == 1
    assert dashboard["longitudinal"]["run_count"] == 2
    alpha = next(item for item in dashboard["longitudinal"]["systems"] if item["entity"] == "omega_alpha_t")
    assert alpha["crystallization_delta"] > 0
    assert alpha["proof_debt_delta"] < 0
    paths = write_dashboard(second, tmp_path / "dashboard", index=index_path)
    assert paths["dashboard_json"].is_file()
    assert "OAK boundary" in paths["dashboard_markdown"].read_text(encoding="utf-8")
