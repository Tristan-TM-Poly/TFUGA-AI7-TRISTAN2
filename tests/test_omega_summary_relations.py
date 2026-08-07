from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.summarizer import SummaryEngine


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "relations-demo"
    root.mkdir()
    (root / "README.md").write_text("# Relations demo\n", encoding="utf-8")

    core = root / "omega_alpha_core_t"
    core.mkdir()
    (core / "README.md").write_text("# Alpha Core\n\nAlpha primitive.\n", encoding="utf-8")
    (core / "core.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")

    product = root / "omega_alpha_product_t"
    product.mkdir()
    (product / "README.md").write_text("# Alpha Product\n\nAlpha product.\n", encoding="utf-8")
    (product / "product.py").write_text("def product():\n    return 2\n", encoding="utf-8")

    tests = root / "tests"
    tests.mkdir()
    (tests / "test_alpha_core_oakbenchmark.py").write_text(
        "from omega_alpha_core_t.core import alpha\n\ndef test_alpha_benchmark():\n    assert alpha() == 1\n",
        encoding="utf-8",
    )

    omega = root / ".omega"
    omega.mkdir()
    (omega / "relations.json").write_text(
        json.dumps(
            {
                "relations": [
                    {
                        "source": "omega_alpha_product_t",
                        "relation": "IMPLEMENTS",
                        "target": "omega_alpha_core_t",
                    },
                    {
                        "source": "omega_alpha_product_t",
                        "relation": "SUPERSEDES",
                        "target": "omega_alpha_core_t",
                    },
                    {
                        "source": "omega_alpha_product_t",
                        "relation": "UNSAFE_INVENTED_RELATION",
                        "target": "omega_alpha_core_t",
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return root


def test_explicit_semantic_relations_require_manifest(tmp_path: Path) -> None:
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    relations = {(edge.source, edge.relation, edge.target) for edge in bundle.edges}
    assert (
        "system:omega_alpha_product_t",
        "IMPLEMENTS",
        "system:omega_alpha_core_t",
    ) in relations
    assert (
        "system:omega_alpha_product_t",
        "SUPERSEDES",
        "system:omega_alpha_core_t",
    ) in relations
    assert not any(relation == "UNSAFE_INVENTED_RELATION" for _, relation, _ in relations)


def test_oakbenchmark_artifact_adds_benchmarks_relation(tmp_path: Path) -> None:
    bundle = SummaryEngine(_repo(tmp_path)).generate(depth=9, audience="oak")
    by_id = {node.id: node for node in bundle.nodes}
    benchmark_edges = [edge for edge in bundle.edges if edge.relation == "BENCHMARKS"]
    assert benchmark_edges
    assert any(
        by_id.get(edge.source) is not None
        and by_id[edge.source].path == "omega_alpha_core_t"
        and by_id.get(edge.target) is not None
        and "oakbenchmark" in by_id[edge.target].path
        for edge in benchmark_edges
    )
