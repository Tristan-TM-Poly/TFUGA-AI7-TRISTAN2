from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3

from omega_discovery_kernel_t import (
    BENCHMARK_FAMILIES,
    KnowledgeFrontierTargets,
    benchmark_registry_manifest,
    iter_benchmark_cases,
    iter_knowledge_frontier_additions,
    plan_knowledge_frontier,
)


def test_benchmark_registry_diversifies_thirty_six_domains() -> None:
    assert len(BENCHMARK_FAMILIES) == 36
    assert len({family.family_id for family in BENCHMARK_FAMILIES}) == 36
    assert len({family.domain for family in BENCHMARK_FAMILIES}) >= 30
    assert all(family.observables for family in BENCHMARK_FAMILIES)
    assert all(family.continuous_generators for family in BENCHMARK_FAMILIES)
    assert all(family.baselines for family in BENCHMARK_FAMILIES)
    assert all(family.metrics for family in BENCHMARK_FAMILIES)
    assert all(family.noise_models for family in BENCHMARK_FAMILIES)
    assert all(family.failure_conditions for family in BENCHMARK_FAMILIES)
    assert all(family.safety_boundary for family in BENCHMARK_FAMILIES)

    manifest = benchmark_registry_manifest()
    assert manifest["family_count"] == 36
    assert len(manifest["families"]) == 36
    assert "raman-spectroscopy" in manifest["domains"]
    assert "knowledge-engineering" in manifest["domains"]
    assert "legal-ip" in manifest["domains"]


def test_benchmark_case_stream_is_deterministic_and_not_materialized() -> None:
    first = list(iter_benchmark_cases(100, seed_offset=17))
    second = list(iter_benchmark_cases(100, seed_offset=17))
    assert first == second
    assert len({case.case_id for case in first}) == 100
    assert len({case.family_id for case in first}) == 36
    assert all(0.0 < case.difficulty <= 1.0 for case in first)
    assert all(case.metadata["status"] == "generated_benchmark_case_not_scientific_result" for case in first)


def test_canonical_targets_equal_50100_logical_additions() -> None:
    targets = KnowledgeFrontierTargets()
    assert targets.validate() == []
    assert targets.cells == 100
    assert targets.claim_count == 1_000
    assert targets.evidence_count == 5_000
    assert targets.experiment_count == 1_000
    assert targets.result_count == 10_000
    assert targets.action_count == 10_000
    assert targets.memory_count == 10_000
    assert targets.identity_count == 1_000
    assert targets.benchmark_cases == 12_000
    assert targets.total_additions == 50_100


def test_addition_stream_emits_exact_diversified_counts() -> None:
    targets = KnowledgeFrontierTargets()
    counts: Counter[str] = Counter()
    namespaces: set[str] = set()
    ids: set[str] = set()
    total = 0
    for addition in iter_knowledge_frontier_additions(targets):
        total += 1
        addition_id = str(addition["addition_id"])
        assert addition_id not in ids
        ids.add(addition_id)
        counts[str(addition["kind"])] += 1
        namespaces.add(str(addition["namespace"]))
        assert addition["provenance"]
        assert addition["metadata"]["oak_status"] == "logical_addition_candidate_not_external_validation"

    assert total == 50_100
    assert counts == Counter(
        {
            "knowledge_cell": 100,
            "claim": 1_000,
            "universal_identity": 1_000,
            "evidence": 5_000,
            "experiment_spec": 1_000,
            "result_packet": 10_000,
            "action_proposal": 10_000,
            "negative_memory": 10_000,
            "benchmark_case": 12_000,
        }
    )
    assert len(namespaces) >= 100


def test_github_dry_run_plans_50100_additions_with_hashes_and_rollback(tmp_path: Path) -> None:
    output = tmp_path / "knowledge-frontier-50100"
    summary = plan_knowledge_frontier(
        output,
        targets=KnowledgeFrontierTargets(),
        initial_shard_bytes=65_536,
        shard_growth_factor=2.0,
        proposed_branch="feat/test-knowledge-frontier-50100",
    )
    report = summary["report"]
    assert summary["count_matches_target"] is True
    assert summary["finite_target_is_not_permanent_ceiling"] is True
    assert summary["remote_mutations"] == 0
    assert summary["targets"]["total_additions"] == 50_100
    assert report["raw_records"] == 50_100
    assert report["unique_additions"] == 50_100
    assert report["duplicates"] == 0
    assert report["invalid_records"] == 0
    assert report["shards"] > 36
    assert report["payload_bytes"] > 1_000_000
    assert report["namespaces"] >= 100
    assert report["no_total_addition_cap"] is True
    assert report["proposed_branch"] == "feat/test-knowledge-frontier-50100"

    required = {
        "benchmark-registry.json",
        "checkpoint.json",
        "commit-plan.jsonl",
        "frontier-index.sqlite3",
        "knowledge-frontier-summary.json",
        "manifest.json",
        "oak-report.json",
        "plan-index.sqlite3",
        "rollback.jsonl",
        "semantic-diff.json",
        "tree.jsonl",
    }
    # GitHubDryRunPlanner names its index plan-index.sqlite3. The frontier-index
    # name is not required here; retain the assertion set dynamically below.
    existing = {path.name for path in output.iterdir()}
    assert required - {"frontier-index.sqlite3"} <= existing
    assert "frontier-index.sqlite3" not in existing
    assert (output / "shards").is_dir()

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    oak = json.loads((output / "oak-report.json").read_text(encoding="utf-8"))
    semantic = json.loads((output / "semantic-diff.json").read_text(encoding="utf-8"))
    registry = json.loads((output / "benchmark-registry.json").read_text(encoding="utf-8"))
    assert manifest["unique_additions"] == 50_100
    assert manifest["no_total_addition_cap"] is True
    assert oak["checks"]["remote_mutations"] == 0
    assert oak["checks"]["rollback_ledger"] is True
    assert semantic["logical_additions"] == 50_100
    assert registry["family_count"] == 36

    tree_lines = sum(1 for _ in (output / "tree.jsonl").open(encoding="utf-8"))
    rollback_lines = sum(1 for _ in (output / "rollback.jsonl").open(encoding="utf-8"))
    commit_lines = sum(1 for _ in (output / "commit-plan.jsonl").open(encoding="utf-8"))
    assert tree_lines == report["shards"]
    assert rollback_lines == report["shards"]
    assert commit_lines == report["shards"]

    with sqlite3.connect(output / "plan-index.sqlite3") as connection:
        fingerprint_count = connection.execute("SELECT COUNT(*) FROM fingerprints").fetchone()[0]
        shard_count = connection.execute("SELECT COUNT(*) FROM shards").fetchone()[0]
    assert fingerprint_count == 50_100
    assert shard_count == report["shards"]


def test_custom_targets_scale_without_a_permanent_total_cap() -> None:
    targets = KnowledgeFrontierTargets(
        cells=1_000,
        claims_per_cell=20,
        evidence_per_claim=10,
        experiments_per_claim=2,
        results_per_experiment=20,
        actions_per_result=2,
        memory_rules_per_result=2,
        identities_per_claim=2,
        benchmark_cases=1_000_000,
    )
    assert targets.validate() == []
    assert targets.total_additions == 5_301_000
    assert targets.total_additions > 5_000_000
    assert not hasattr(targets, "max_total_additions")
