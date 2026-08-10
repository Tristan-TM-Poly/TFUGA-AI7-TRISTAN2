from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_intent_t import Intent, IntentCompiler, LogicalFrontier, WorkPlanner
from omega_intent_t.cli import main


def sample_intent() -> Intent:
    return Intent.from_mapping({
        "objective": "Develop and compare Tristan fractal transforms against classical baselines.",
        "expected_outputs": [
            "theory_documents",
            "mathematical_specifications",
            "code",
            "tests",
            "benchmarks",
            "reports",
            "product_analysis",
            "ip_analysis",
        ],
        "languages": ["python", "rust", "cpp"],
        "mode": "expansive",
    })


def test_intent_identity_is_deterministic() -> None:
    first = sample_intent()
    second = sample_intent()
    assert first.intent_id == second.intent_id
    assert first.intent_id.startswith("INTENT-")


def test_frontier_is_large_reversible_and_not_materialized() -> None:
    frontier = LogicalFrontier()
    assert frontier.size > 1_000_000_000
    assert frontier.manifest()["permanent_total_cap"] is None
    for index in (0, 1, 42, 1_000_000, frontier.size - 1):
        assert frontier.encode(frontier.decode(index)) == index
    assert list(frontier.iter_range(10, 3))[0][0] == 10


def test_work_plan_is_acyclic_and_covers_requirements() -> None:
    intent = sample_intent()
    planner = WorkPlanner()
    requirements = planner.derive_requirements(intent)
    units = planner.plan(intent, requirements)
    batches = planner.topological_batches(units)
    covered = {rid for unit in units for rid in unit.requirement_ids}
    assert {req.requirement_id for req in requirements}.issubset(covered)
    assert sum(len(batch) for batch in batches) == len(units)


def test_compile_emits_traceable_bundle_and_scaffolds(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    result = IntentCompiler().compile(sample_intent(), root, materialize_scaffolds=True)
    assert result.oak_report.passed is True
    assert result.additions > 0
    assert (root / "intent.json").is_file()
    assert (root / "requirements.jsonl").is_file()
    assert (root / "work-units.jsonl").is_file()
    assert (root / "generator-specs.jsonl").is_file()
    assert (root / "hypergraph.json").is_file()
    assert (root / "hypergraph.graphml").is_file()
    assert (root / "reports" / "oak.json").is_file()
    assert (root / "next-intent.json").is_file()
    assert list((root / "scaffolds" / "python").glob("*.py"))
    oak = json.loads((root / "reports" / "oak.json").read_text())
    assert oak["theorem_claimed"] is False
    assert oak["remote_mutations"] == 0
    graph = json.loads((root / "hypergraph.json").read_text())
    assert graph["summary"]["validation_errors"] == []


def test_compile_refuses_nonempty_output(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "keep.txt").write_text("do not overwrite")
    with pytest.raises(FileExistsError):
        IntentCompiler().compile(sample_intent(), root)


def test_cli_campaign_streams_exact_slice(tmp_path: Path) -> None:
    path = tmp_path / "campaign.jsonl"
    assert main(["campaign", "--offset", "123", "--count", "257", "--output", str(path)]) == 0
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 257
    assert rows[0]["payload"]["logical_index"] == 123
    assert rows[-1]["payload"]["logical_index"] == 379
    assert len({row["addition_id"] for row in rows}) == 257
    assert all(row["metadata"]["executed"] is False for row in rows)


def test_github_planner_bridge(tmp_path: Path) -> None:
    pytest.importorskip("omega_unbounded_t.github_planner")
    root = tmp_path / "bundle"
    result = IntentCompiler().compile(sample_intent(), root, github_plan=True)
    assert result.github_plan is not None
    assert result.github_plan["no_total_addition_cap"] is True
    assert result.github_plan["unique_additions"] == result.additions
    assert (root / "github-plan" / "manifest.json").is_file()
