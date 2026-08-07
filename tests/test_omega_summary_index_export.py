from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.cli import main
from omega_summary_fractal_t.export import write_graph_exports
from omega_summary_fractal_t.index import (
    append_snapshot,
    longitudinal_metrics,
    normalize_snapshot,
    verify_index,
)


def repository_payload(*, fingerprint: str, status: str, tests: int, workflows: int) -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-07T15:00:00Z",
        "root": "demo",
        "depth": 9,
        "audience": "oak",
        "focus": None,
        "nodes": [
            {
                "id": "system:omega_alpha_t",
                "kind": "system",
                "path": "omega_alpha_t",
                "title": "Omega Alpha",
                "one_line": "Alpha engine",
                "status": status,
                "tags": [],
                "metrics": {
                    "documents": 1,
                    "documented": True,
                    "code_files": 2,
                    "implemented": True,
                    "tests": tests,
                    "tested": bool(tests),
                    "workflows": workflows,
                    "schemas": 1,
                    "schema_backed": True,
                    "first_seen": "2026-08-01T12:00:00-04:00",
                },
                "evidence": [],
                "children": [],
            },
            {
                "id": "file:tests-test-alpha.py",
                "kind": "test",
                "path": "tests/test_alpha.py",
                "title": "test_alpha.py",
                "one_line": "test file",
                "status": "observed",
                "tags": [],
                "metrics": {},
                "evidence": [],
                "children": [],
            },
        ],
        "edges": [
            {
                "source": "system:omega_alpha_t",
                "target": "file:tests-test-alpha.py",
                "relation": "TESTS",
            }
        ],
        "health": {},
        "gaps": [],
        "duplicate_candidates": [],
        "cache_fingerprint": fingerprint,
    }


def test_index_is_hash_chained_and_idempotent(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    first = repository_payload(fingerprint="a" * 64, status="implemented", tests=0, workflows=0)
    second = repository_payload(fingerprint="b" * 64, status="tested", tests=1, workflows=1)
    index = append_snapshot(index_path, first)
    assert verify_index(index)
    assert len(index["runs"]) == 1
    index = append_snapshot(index_path, first)
    assert len(index["runs"]) == 1
    index = append_snapshot(index_path, second)
    assert verify_index(index)
    assert len(index["runs"]) == 2
    assert index["runs"][1]["previous_hash"] == index["runs"][0]["entry_hash"]


def test_longitudinal_metrics_detect_crystallization(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    append_snapshot(
        index_path,
        repository_payload(fingerprint="c" * 64, status="implemented", tests=0, workflows=0),
    )
    index = append_snapshot(
        index_path,
        repository_payload(fingerprint="d" * 64, status="tested", tests=1, workflows=1),
    )
    report = longitudinal_metrics(index)
    row = report["systems"][0]
    assert row["status_first"] == "implemented"
    assert row["status_last"] == "tested"
    assert row["crystallization_delta"] > 0
    assert row["proof_debt_delta"] < 0
    assert row["status_transitions"] == [{"run": 2, "from": "implemented", "to": "tested"}]
    assert "not scientific progress" in report["boundary"]


def test_normalize_corpus_payload() -> None:
    payload = {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-07T15:00:00Z",
        "fingerprint": "e" * 64,
        "repositories": [
            {
                "name": "repo-a",
                "available": True,
                "systems": [
                    {
                        "path": "omega_alpha_t",
                        "status": "tested",
                        "metrics": {"code_files": 1, "tests": 1, "workflows": 1, "documents": 1},
                    }
                ],
            }
        ],
        "cross_repo_links": [],
    }
    normalized = normalize_snapshot(payload)
    assert normalized["source_kind"] == "corpus"
    assert "repo-a::omega_alpha_t" in normalized["entities"]


def test_graph_exports_are_machine_readable(tmp_path: Path) -> None:
    payload = repository_payload(fingerprint="f" * 64, status="tested", tests=1, workflows=1)
    paths = write_graph_exports(payload, tmp_path / "graph")
    jsonl_lines = paths["jsonl"].read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["record_type"] == "node" for line in jsonl_lines)
    assert any(json.loads(line)["record_type"] == "edge" for line in jsonl_lines)
    graphml = paths["graphml"].read_text(encoding="utf-8")
    assert "<graphml" in graphml
    assert "TESTS" in graphml
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["node_count"] == 2
    assert manifest["edge_count"] == 1


def test_index_and_export_cli(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(repository_payload(fingerprint="1" * 64, status="tested", tests=1, workflows=1)),
        encoding="utf-8",
    )
    index_path = tmp_path / "history" / "index.json"
    report_dir = tmp_path / "history" / "reports"
    assert main(
        [
            "index",
            str(summary),
            "--index-file",
            str(index_path),
            "--report-dir",
            str(report_dir),
        ]
    ) == 0
    assert index_path.exists()
    assert (report_dir / "LONGITUDINAL_CRYSTALLIZATION.json").exists()
    assert (report_dir / "LONGITUDINAL_CRYSTALLIZATION.md").exists()

    graph_dir = tmp_path / "graph"
    assert main(["export", str(summary), "--output-dir", str(graph_dir)]) == 0
    assert (graph_dir / "SUMMARY_GRAPH.jsonl").exists()
    assert (graph_dir / "SUMMARY_GRAPH.graphml").exists()
