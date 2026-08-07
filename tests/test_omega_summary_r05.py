from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_summary_fractal_t.aliases import (
    approve_alias,
    identity_proposals,
    resolve_alias,
    verify_alias_registry,
)
from omega_summary_fractal_t.fleet import (
    append_fleet_history,
    build_fleet_manifest,
    render_fleet_html,
    verify_fleet_history,
)
from omega_summary_fractal_t.query_plan import execute_query_plan


def _node(path: str, status: str, *, tests=0, workflows=0, documents=1, schemas=0, code=1):
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
        "evidence": [],
    }


def _summary(nodes, *, root="private-repository-name", fingerprint="fp"):
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-07T12:00:00Z",
        "root": root,
        "depth": 9,
        "audience": "oak",
        "focus": None,
        "nodes": nodes,
        "edges": [],
        "health": {},
        "gaps": [],
        "duplicate_candidates": [],
        "cache_fingerprint": fingerprint,
    }


def _corpus(repository_names: list[str]):
    repositories = []
    for index, name in enumerate(repository_names):
        system = _node(f"omega_private_{index}_t", "implemented")
        repositories.append(
            {
                "name": name,
                "available": True,
                "fingerprint": f"fp-{index}",
                "health": {},
                "systems": [
                    {
                        "path": system["path"],
                        "title": system["title"],
                        "one_line": system["one_line"],
                        "status": system["status"],
                        "metrics": system["metrics"],
                    }
                ],
                "gap_count": 0,
            }
        )
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-07T12:00:00Z",
        "depth": 9,
        "audience": "oak",
        "repositories": repositories,
        "totals": {"repositories": len(repositories), "systems": len(repositories)},
        "gaps": [],
        "duplicate_candidates": [],
        "cross_repo_links": [],
        "fingerprint": "corpus-fp",
    }


def test_fleet_projection_is_stable_and_does_not_serialize_raw_names():
    payload = _summary([
        _node("omega_secret_alpha_t", "tested", tests=1, workflows=1, schemas=1),
        _node("omega_secret_beta_t", "implemented"),
    ])
    first = build_fleet_manifest(payload, salt="runtime-secret-a")
    second = build_fleet_manifest(payload, salt="runtime-secret-a")
    other_salt = build_fleet_manifest(payload, salt="runtime-secret-b")
    assert first == second
    assert first["repositories"][0]["repository_token"] != other_salt["repositories"][0]["repository_token"]
    assert first["fleet_id"] != other_salt["fleet_id"]
    serialized = json.dumps(first, sort_keys=True)
    rendered = render_fleet_html(first)
    for forbidden in ("private-repository-name", "omega_secret_alpha_t", "omega_secret_beta_t", "runtime-secret-a"):
        assert forbidden not in serialized
        assert forbidden not in rendered
    assert first["privacy"]["raw_repository_names_serialized"] is False
    assert first["privacy"]["salt_serialized"] is False
    assert len(first["fingerprint"]) == 64


def test_fleet_id_is_stable_when_repository_membership_changes():
    one_repo = build_fleet_manifest(_corpus(["private-a"]), salt="stable-scope-salt")
    two_repos = build_fleet_manifest(_corpus(["private-a", "private-b"]), salt="stable-scope-salt")
    assert one_repo["fleet_id"] == two_repos["fleet_id"]
    assert one_repo["fingerprint"] != two_repos["fingerprint"]
    assert one_repo["totals"]["repositories"] == 1
    assert two_repos["totals"]["repositories"] == 2


def test_fleet_history_is_hash_chained_idempotent_and_private(tmp_path: Path):
    first = build_fleet_manifest(
        _summary([_node("omega_secret_alpha_t", "implemented")], fingerprint="fp1"),
        salt="stable-runtime-salt",
    )
    second = build_fleet_manifest(
        _summary([_node("omega_secret_alpha_t", "tested", tests=1, workflows=1, schemas=1)], fingerprint="fp2"),
        salt="stable-runtime-salt",
    )
    history_path = tmp_path / "FLEET_HISTORY.json"
    history = append_fleet_history(history_path, first)
    history = append_fleet_history(history_path, second)
    history = append_fleet_history(history_path, second)
    assert verify_fleet_history(history)
    assert len(history["runs"]) == 2
    serialized = history_path.read_text(encoding="utf-8")
    assert "private-repository-name" not in serialized
    assert "omega_secret_alpha_t" not in serialized
    assert "stable-runtime-salt" not in serialized


def test_alias_registry_requires_explicit_approval_and_is_hash_chained(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1786111200")
    registry_path = tmp_path / "aliases.json"
    registry = approve_alias(
        registry_path,
        source="omega_old_t",
        target="omega_new_t",
        evidence_ref="IDENTITY_CONTINUITY.json#candidate-1",
        approved_by="reviewer",
    )
    assert verify_alias_registry(registry)
    assert resolve_alias("omega_old_t", registry) == "omega_new_t"
    duplicate = approve_alias(
        registry_path,
        source="omega_old_t",
        target="omega_new_t",
        evidence_ref="IDENTITY_CONTINUITY.json#candidate-1",
        approved_by="reviewer",
    )
    assert len(duplicate["entries"]) == 1

    registry = approve_alias(
        registry_path,
        source="omega_new_t",
        target="omega_latest_t",
        evidence_ref="manual-review-2",
        approved_by="reviewer",
    )
    assert resolve_alias("omega_old_t", registry) == "omega_latest_t"
    with pytest.raises(ValueError, match="cycle"):
        approve_alias(
            registry_path,
            source="omega_latest_t",
            target="omega_old_t",
            evidence_ref="bad-cycle",
            approved_by="reviewer",
        )


def test_identity_candidates_remain_non_authoritative_proposals():
    report = {
        "candidates": [
            {
                "from": "omega_old_t",
                "to": "omega_new_t",
                "score": 1.0,
                "evidence": "exact_content_signature",
                "one_to_one": True,
                "status": "review_required",
                "automatic_rewrite": False,
            }
        ]
    }
    proposals = identity_proposals(report)
    assert proposals["proposals"][0]["source"] == "omega_old_t"
    assert proposals["proposals"][0]["target"] == "omega_new_t"
    assert proposals["proposals"][0]["automatic_approval"] is False
    assert proposals["proposals"][0]["status"] == "proposal_only"


def test_query_plan_composes_boolean_filters_groups_and_aggregates():
    payload = _summary([
        _node("omega_alpha_t", "tested", tests=1, workflows=1, schemas=1),
        _node("omega_beta_t", "implemented"),
        _node("omega_gamma_t", "implemented"),
        _node("omega_docs_only_t", "documented", code=0),
    ], root="demo")
    plan = {
        "seed": {"kind": "system"},
        "where": [{"field": "structural_crystallization", "op": "gte", "value": 0.4}],
        "any": [
            {"field": "status", "op": "eq", "value": "tested"},
            {"field": "status", "op": "eq", "value": "implemented"},
        ],
        "not": [{"field": "path", "op": "contains", "value": "gamma"}],
        "group_by": ["status"],
        "aggregates": [
            {"name": "count", "op": "count"},
            {"name": "mean_c", "op": "mean", "field": "structural_crystallization"},
        ],
        "sort": [{"field": "count", "direction": "desc"}],
        "limit": 10,
    }
    report = execute_query_plan(payload, plan)
    assert report["total_matches"] == 2
    groups = {item["status"]: item for item in report["groups"]}
    assert groups["tested"]["count"] == 1
    assert groups["implemented"]["count"] == 1
    assert groups["tested"]["mean_c"] == 1.0
    assert groups["implemented"]["mean_c"] == 0.4
    assert "authority" in report["boundary"]
