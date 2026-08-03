from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_depth_t import DepthGraph, NodeContract, OakStatus, build_oakgate_depth9
from omega_depth_t.registry import creation_roots, find_root
from omega_depth_t.scaffold import scaffold_roots


def test_registry_has_40_unique_roots() -> None:
    roots = creation_roots()
    assert len(roots) == 40
    assert len({root.slug for root in roots}) == 40
    assert len({root.node_id for root in roots}) == 40
    assert find_root("omega-doc-t").name.startswith("Ω-DOC-T")
    assert find_root("omega_doc_t").slug == "omega-doc-t"


def test_node_contract_round_trip() -> None:
    node = NodeContract(id="root", name="Root", depth=0, path="root", parent_id=None, root_creation="Root", role="Test root", oak_status=OakStatus.DEFINED)
    assert NodeContract.from_dict(node.to_dict()) == node


def test_non_root_requires_parent() -> None:
    with pytest.raises(ValueError, match="requires parent_id"):
        NodeContract(id="bad", name="Bad", depth=1, path="bad", parent_id=None, root_creation="Bad", role="Invalid")


def test_graph_rejects_child_before_parent() -> None:
    child = NodeContract(id="root.child", name="Child", depth=1, path="root/child", parent_id="root", root_creation="Root", role="Child")
    graph = DepthGraph()
    with pytest.raises(ValueError, match="parent must be added first"):
        graph.add(child)


def test_oakgate_example_is_valid_and_reaches_depth_9() -> None:
    graph = build_oakgate_depth9()
    assert graph.maximum_observed_depth == 9
    assert len(graph) >= 80
    assert not graph.validate()
    evidence = graph.get("oakgate.oak_code.test_inspector.coverage_analyzer.branch_coverage.missing_branch_detector.compare_expected_to_observed.test_one_branch_missing.then_provenance.residuals")
    assert evidence.depth == 9
    assert evidence.is_atomic_candidate


def test_oakgate_navigation() -> None:
    graph = build_oakgate_depth9()
    node_id = "oakgate.oak_code.test_inspector.coverage_analyzer.branch_coverage.missing_branch_detector"
    assert {item.name for item in graph.children(node_id)} >= {"compare_expected_to_observed()", "emit_gap_record()"}
    ancestors = graph.ancestors(node_id)
    assert ancestors[0].id == "oakgate"
    assert ancestors[-1].id.endswith("branch_coverage")


def test_bundle_exports_all_formats(tmp_path: Path) -> None:
    graph = build_oakgate_depth9()
    artifacts = graph.write_bundle(tmp_path)
    assert set(artifacts) == {"json", "jsonl", "markdown", "graphml", "report"}
    restored = DepthGraph.read_json(tmp_path / "depth-graph.json")
    assert restored.summary() == graph.summary()
    report = json.loads((tmp_path / "oak-report.json").read_text(encoding="utf-8"))
    assert report["validation_issue_count"] == 0
    assert "not a permanent architecture ceiling" in report["boundary"]


def test_scaffold_all_roots(tmp_path: Path) -> None:
    result = scaffold_roots(tmp_path)
    assert result["root_count"] == 40
    registry = json.loads((tmp_path / "root-registry.json").read_text(encoding="utf-8"))
    assert registry["root_count"] == 40
    assert (tmp_path / "01_hgfm" / "node.json").exists()
    assert (tmp_path / "40_omega-jkd-t" / "README.md").exists()
