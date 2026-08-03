from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from omega_histosci_hg_t import (
    EdgeKind,
    EpistemicStatus,
    HistoricalHyperedge,
    HistoricalHypergraph,
    HistoricalNode,
    NodeKind,
    OAKEvidence,
    TemporalLayer,
    assess_evidence,
    build_report,
    build_seed,
)
from omega_histosci_hg_t.registry import HistoryRegistry
from omega_histosci_hg_t.models import BranchRecord


def test_seed_audits_are_valid() -> None:
    graph, registry = build_seed()
    assert graph.audit().valid
    assert registry.audit().valid


def test_seed_has_broad_science_coverage() -> None:
    _, registry = build_seed()
    assert len(registry.roots()) == 10
    assert len(registry.branches) >= 100
    required = {
        "mathematics.analysis",
        "physics.quantum",
        "chemistry.analytical",
        "earth_space.meteorology_climate",
        "life.genetics_genomics",
        "medicine.epidemiology",
        "computing.ai",
        "engineering.physical",
        "social.history_archaeology",
        "metascience.reproducibility",
    }
    assert required <= set(registry.branches)


def test_spectroscopy_has_multiple_parents() -> None:
    _, registry = build_seed()
    branch = registry.branches["physics.optics.spectroscopy"]
    assert branch.parent_branch_ids == ("physics.optics", "chemistry.analytical")
    assert "mminus.spectroscopy.overfit" in branch.negative_memory_ids


def test_negative_memory_is_actionable() -> None:
    _, registry = build_seed()
    memory = registry.negative_memories["mminus.spectroscopy.overfit"]
    assert memory.fertile_for_method is True
    assert "identifiability" in memory.lesson.lower()


def test_report_is_deterministic() -> None:
    first = build_report()
    second = build_report()
    assert first == second
    assert len(first["digest"]) == 64


def test_report_refuses_truth_and_exhaustiveness_claims() -> None:
    report = build_report()
    assert report["historical_truth_certified"] is False
    assert report["source_completeness_claimed"] is False
    assert report["global_exhaustiveness_claimed"] is False
    assert report["decolonial_completeness_claimed"] is False
    assert report["permanent_total_cap"] is None


def test_oak_high_quality_evidence_is_established() -> None:
    evidence = OAKEvidence(0.98, 0.95, 0.92, 0.90, 0.05, source_count=8)
    result = assess_evidence(evidence)
    assert result.status is EpistemicStatus.ESTABLISHED
    assert result.score >= 0.82
    assert result.software_validation_only


def test_oak_no_source_caps_status() -> None:
    evidence = OAKEvidence(1.0, 1.0, 1.0, 1.0, 0.0, source_count=0)
    result = assess_evidence(evidence)
    assert result.status in {EpistemicStatus.UNCERTAIN, EpistemicStatus.CONTESTED}
    assert "no source is attached" in result.reasons


def test_hyperedge_rejects_overlap() -> None:
    with pytest.raises(ValueError, match="both source and target"):
        HistoricalHyperedge("edge.bad", EdgeKind.ENABLED_BY, ("n1",), ("n1",))


def test_graph_rejects_missing_nodes() -> None:
    graph = HistoricalHypergraph()
    graph.add_node(HistoricalNode("n1", "Node 1", NodeKind.CONCEPT))
    with pytest.raises(KeyError, match="missing nodes"):
        graph.add_edge(HistoricalHyperedge("e1", EdgeKind.ENABLED_BY, ("n1",), ("n2",)))


def test_duplicate_hyperedge_signatures_are_audited() -> None:
    graph = HistoricalHypergraph()
    graph.add_node(HistoricalNode("n1", "Node 1", NodeKind.CONCEPT))
    graph.add_node(HistoricalNode("n2", "Node 2", NodeKind.CONCEPT))
    graph.add_edge(HistoricalHyperedge("e1", EdgeKind.ENABLED_BY, ("n1",), ("n2",)))
    graph.add_edge(HistoricalHyperedge("e2", EdgeKind.ENABLED_BY, ("n1",), ("n2",)))
    audit = graph.audit()
    assert not audit.valid
    assert audit.duplicate_edge_signatures == ("e1", "e2")


def test_reachability_includes_hypergraph_successors() -> None:
    graph, _ = build_seed()
    reached = graph.reachable(("instrument::prism",), max_depth=3)
    assert "instrument::spectroscope" in reached
    assert "branch::physics.optics.spectroscopy" in reached


def test_temporal_slice_retains_relevant_nodes() -> None:
    graph, _ = build_seed()
    sliced = graph.temporal_slice((TemporalLayer.TWENTIETH_CENTURY,))
    node_ids = {node.node_id for node in sliced.nodes}
    assert "branch::physics.quantum.mechanics" in node_ids
    assert "concept::transition_energy" in node_ids


def test_graphml_is_deterministic_and_incidence_expanded() -> None:
    graph, _ = build_seed()
    first = graph.to_graphml()
    second = graph.to_graphml()
    assert first == second
    assert "hyperedge::" in first
    assert "omega-histoscience" in first


def test_lineage_and_children() -> None:
    _, registry = build_seed()
    ancestors = registry.ancestors_of("physics.optics.spectroscopy")
    assert "physics.optics" in ancestors
    assert "science.physics" in ancestors
    children = {branch.branch_id for branch in registry.children_of("physics.optics")}
    assert "physics.optics.spectroscopy" in children


def test_registry_detects_parent_cycle() -> None:
    registry = HistoryRegistry()
    registry.add_branch(BranchRecord("a", "A", ("b",), ("problem a",)))
    registry.add_branch(BranchRecord("b", "B", ("a",), ("problem b",)))
    audit = registry.audit()
    assert not audit.valid
    assert audit.parent_cycles


def test_cli_audit_and_stats(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    stats_path = tmp_path / "stats.json"
    subprocess.run(
        [sys.executable, "-m", "omega_histosci_hg_t.cli", "audit", "--output", str(audit_path)],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "omega_histosci_hg_t.cli", "stats", "--output", str(stats_path)],
        check=True,
    )
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    assert audit["status"] == "CERTIFIED_SOFTWARE_HISTORY_GRAPH_FIXTURES_R0_1"
    assert stats["branches"] >= 100
    assert stats["permanent_total_cap"] is None


def test_cli_graphml(tmp_path: Path) -> None:
    output = tmp_path / "seed.graphml"
    subprocess.run(
        [sys.executable, "-m", "omega_histosci_hg_t.cli", "export-graphml", "--output", str(output)],
        check=True,
    )
    assert output.read_text(encoding="utf-8").startswith("<?xml")


def test_cli_lineage(tmp_path: Path) -> None:
    output = tmp_path / "lineage.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "omega_histosci_hg_t.cli",
            "lineage",
            "physics.optics.spectroscopy",
            "--output",
            str(output),
        ],
        check=True,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "science.physics" in payload["ancestors"]


def test_exact_seed_counts_are_stable() -> None:
    graph, registry = build_seed()
    assert len(registry.branches) == 114
    assert len(graph.nodes) == 123
    assert len(graph.edges) == 110
