from __future__ import annotations

import hashlib
import json

import pytest

from omega_unbounded_t import (
    GitHubDryRunPlanner,
    GitHubPlanPolicy,
    synthetic_additions,
)


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_streaming_planner_handles_tens_of_thousands_without_total_cap(tmp_path):
    output = tmp_path / "plan"
    report = GitHubDryRunPlanner(
        output,
        policy=GitHubPlanPolicy(initial_shard_bytes=8_192, shard_growth_factor=2.0),
        proposed_branch="feat/generated-40000",
    ).plan(synthetic_additions(40_000, namespaces=4))

    assert report.status == "planned"
    assert report.raw_records == 40_000
    assert report.unique_additions == 40_000
    assert report.duplicates == 0
    assert report.invalid_records == 0
    assert report.namespaces == 4
    assert report.shards > 4
    assert report.no_total_addition_cap is True
    assert report.proposed_branch == "feat/generated-40000"

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    tree = _jsonl(output / "tree.jsonl")
    commit_plan = _jsonl(output / "commit-plan.jsonl")
    rollback = _jsonl(output / "rollback.jsonl")
    oak = json.loads((output / "oak-report.json").read_text(encoding="utf-8"))

    assert manifest["no_total_addition_cap"] is True
    assert manifest["policy"]["initial_shard_bytes"] == 8_192
    assert len(tree) == report.shards
    assert len(commit_plan) == report.shards
    assert len(rollback) == report.shards
    assert oak["checks"]["remote_mutations"] == 0
    assert oak["checks"]["disk_backed_deduplication"] is True

    for shard in tree:
        path = output / shard["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == shard["sha256"]
        assert shard["additions"] > 0

    budgets_by_stream: dict[tuple[str, str], list[int]] = {}
    for shard in tree:
        budgets_by_stream.setdefault((shard["namespace"], shard["kind"]), []).append(shard["byte_budget_used"])
    assert all(values == sorted(values) for values in budgets_by_stream.values())
    assert any(len(set(values)) > 1 for values in budgets_by_stream.values())


def test_duplicates_invalid_records_and_sensitive_risks_are_routed(tmp_path):
    output = tmp_path / "plan"
    records = [
        {
            "addition_id": "a",
            "namespace": "physics",
            "kind": "claim",
            "payload": {"statement": "same"},
            "provenance": ["source://one"],
            "risk": "ip_sensitive",
        },
        {
            "addition_id": "b",
            "namespace": "physics",
            "kind": "claim",
            "payload": {"statement": "same"},
            "provenance": ["source://one"],
        },
        {
            "addition_id": "c",
            "namespace": "physics",
            "kind": "test",
            "payload": {"expected": True},
            "provenance": ["source://two"],
        },
        {
            "addition_id": "invalid",
            "namespace": "physics",
            "payload": ["not", "an", "object"],
        },
    ]

    report = GitHubDryRunPlanner(output).plan(records)

    assert report.raw_records == 4
    assert report.unique_additions == 2
    assert report.duplicates == 1
    assert report.invalid_records == 1
    assert report.approval_required_additions == 1
    assert len(_jsonl(output / "duplicates.jsonl")) == 1
    assert len(_jsonl(output / "quarantine.jsonl")) == 1
    assert len(_jsonl(output / "m_minus.jsonl")) == 1
    assert any(item["requires_human_approval"] for item in _jsonl(output / "commit-plan.jsonl"))


def test_provenance_policy_quarantines_unprovenanced_records(tmp_path):
    output = tmp_path / "plan"
    report = GitHubDryRunPlanner(
        output,
        policy=GitHubPlanPolicy(require_provenance=True),
    ).plan(
        [
            {
                "addition_id": "missing-source",
                "namespace": "general",
                "kind": "claim",
                "payload": {"statement": "unprovenanced"},
            }
        ]
    )

    assert report.unique_additions == 0
    assert report.invalid_records == 1
    assert report.shards == 0
    assert json.loads((output / "oak-report.json").read_text(encoding="utf-8"))["status"] == "PASS_WITH_QUARANTINE"


def test_existing_nonempty_output_is_never_overwritten(tmp_path):
    output = tmp_path / "plan"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError):
        GitHubDryRunPlanner(output).plan(synthetic_additions(1))

    assert marker.read_text(encoding="utf-8") == "preserve"
