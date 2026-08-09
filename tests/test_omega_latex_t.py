from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from omega_latex_t import (
    DocumentCompiler,
    DocumentIR,
    audit_document,
    evidence_matrix,
    infer_dimension,
    notation_registry,
    notation_rename_plan,
    parse_unit,
    project_depth,
    rebuild_plan,
    render_math,
    write_theorem_bundle,
)


FIXTURE = {
    "meta": {"title": "Test", "author": "Omega", "language": "en"},
    "sources": [{"id": "src.1", "citation": "fixture"}],
    "results": {"metric.value": "12.5%"},
    "nodes": [
        {"id": "sec", "kind": "section", "title": "Core"},
        {
            "id": "def.x",
            "kind": "definition",
            "content": "An evidence-bound object.",
            "status": "draft",
        },
        {
            "id": "eq.x",
            "kind": "equation",
            "content": "x = y + z",
            "dependencies": ["def.x"],
            "sources": ["src.1"],
            "dimension_lhs": "L",
            "dimension_rhs": "L",
        },
        {
            "id": "claim.x",
            "kind": "claim",
            "content": "A bounded claim.",
            "dependencies": ["eq.x"],
            "status": "draft",
        },
        {
            "id": "result.x",
            "kind": "result",
            "content": "A measured value injected from the result registry.",
            "dependencies": ["claim.x"],
            "status": "draft",
            "result_key": "metric.value",
        },
    ],
}


class OmegaLatexTests(unittest.TestCase):
    def test_deterministic_render_and_hash(self):
        doc = DocumentIR.from_mapping(FIXTURE)
        compiler = DocumentCompiler()
        a = compiler.render(doc)
        b = compiler.render(doc)
        self.assertEqual(a.latex, b.latex)
        self.assertEqual(a.latex_hash, b.latex_hash)
        self.assertTrue(a.audit.passed)
        self.assertIn(r"\begin{equation}", a.latex)
        self.assertIn("semantic-hash:", a.latex)
        self.assertIn(r"\Result{metric.value}", a.latex)

    def test_dependency_sort(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"] = list(reversed(raw["nodes"]))
        order = [
            x.id
            for x in DocumentCompiler().topological_nodes(DocumentIR.from_mapping(raw))
        ]
        self.assertLess(order.index("def.x"), order.index("eq.x"))
        self.assertLess(order.index("eq.x"), order.index("claim.x"))

    def test_missing_dependency_fails_closed(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][1]["dependencies"] = ["missing"]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertFalse(report.passed)
        self.assertIn("DOCIR_MISSING_DEPENDENCY", {x.code for x in report.errors})

    def test_cycle_is_detected(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][1]["dependencies"] = ["claim.x"]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("DEPENDENCY_CYCLE", {x.code for x in report.errors})

    def test_dimension_mismatch(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["dimension_rhs"] = "T"
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("DIMENSION_MISMATCH", {x.code for x in report.errors})

    def test_symbol_collision_warning(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][1]["symbols"] = [{"symbol": "G", "meaning": "graph"}]
        raw["nodes"][2]["symbols"] = [{"symbol": "G", "meaning": "generator"}]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertTrue(report.passed)
        self.assertIn("SYMBOL_COLLISION", {x.code for x in report.warnings})

    def test_proven_theorem_requires_proof(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"].append(
            {
                "id": "thm",
                "kind": "theorem",
                "content": "A theorem.",
                "status": "proven",
                "dependencies": ["def.x"],
            }
        )
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("PROOF_MISSING", {x.code for x in report.errors})

    def test_proven_theorem_with_reverse_proof_link(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"].extend(
            [
                {
                    "id": "thm",
                    "kind": "theorem",
                    "content": "A theorem.",
                    "status": "proven",
                    "dependencies": ["def.x"],
                },
                {
                    "id": "proof.thm",
                    "kind": "proof",
                    "content": "Proof body.",
                    "dependencies": ["thm"],
                },
            ]
        )
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertNotIn("PROOF_MISSING", {x.code for x in report.errors})

    def test_build_writes_extended_evidence_bundle(self):
        doc = DocumentIR.from_mapping(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            artifact = DocumentCompiler().build_to(doc, td)
            paths = {p.name for p in Path(td).iterdir()}
            self.assertTrue(
                {
                    "document.tex",
                    "docir.json",
                    "oak-report.json",
                    "manifest.json",
                    "m_minus.jsonl",
                    "notation-registry.json",
                    "notation-rename-plan.json",
                    "evidence-matrix.json",
                }
                <= paths
            )
            manifest = json.loads((Path(td) / "manifest.json").read_text())
            self.assertEqual(manifest["semantic_hash"], artifact.semantic_hash)
            self.assertTrue(manifest["oak_passed"])

    def test_markdown_adapter_is_conservative(self):
        from omega_latex_t.adapters import markdown_to_document

        doc = markdown_to_document("# Intro\n\nText.\n\n$$\nx = y\n$$\n", title="M")
        self.assertEqual(
            [n.kind.value for n in doc.nodes], ["section", "paragraph", "equation"]
        )
        self.assertTrue(all(n.status == "imported" for n in doc.nodes))

    def test_summary_adapter_preserves_edges_as_metadata(self):
        from omega_latex_t.adapters import summary_bundle_to_document

        doc = summary_bundle_to_document(
            {
                "root": "repo",
                "nodes": [{"id": "a", "title": "A", "kind": "module"}],
                "edges": [{"source": "a", "target": "b", "relation": "imports"}],
            }
        )
        self.assertEqual(len(doc.nodes), 2)
        self.assertEqual(doc.provenance["summary_edges"][0]["relation"], "imports")
        self.assertFalse(doc.nodes[1].dependencies)

    def test_github_snapshot_provenance(self):
        from omega_latex_t.adapters import github_snapshot_to_document

        doc = github_snapshot_to_document(
            {
                "repository": "owner/repo",
                "pull_requests": [
                    {
                        "number": 7,
                        "title": "X",
                        "url": "https://example.test/pr/7",
                        "state": "open",
                    }
                ],
                "files": [{"path": "a.py", "additions": 3, "deletions": 1}],
            }
        )
        self.assertEqual(doc.sources[0].id, "github.pr.7")
        self.assertIn("engineering evidence", doc.provenance["boundary"])

    def test_github_pr_event_adapter_is_offline_normalizer(self):
        from omega_latex_t.adapters import github_pr_event_to_document

        doc = github_pr_event_to_document(
            {
                "action": "synchronize",
                "number": 9,
                "repository": {"full_name": "owner/repo"},
                "pull_request": {
                    "number": 9,
                    "title": "Delta",
                    "state": "open",
                    "draft": True,
                    "html_url": "https://example.test/pr/9",
                    "head": {"sha": "abc"},
                    "base": {"sha": "def"},
                },
            }
        )
        self.assertEqual(doc.provenance["event_action"], "synchronize")
        self.assertEqual(doc.sources[0].id, "github.pr.9")

    def test_semantic_delta_dependency_closure(self):
        from omega_latex_t.delta import semantic_delta

        before = DocumentIR.from_mapping(FIXTURE)
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["content"] = "x = y - z"
        after = DocumentIR.from_mapping(raw)
        delta = semantic_delta(before, after)
        self.assertIn("eq.x", delta["changed"])
        self.assertIn("claim.x", delta["affected_after"])
        self.assertIn("result.x", delta["affected_after"])
        self.assertTrue(delta["rebuild_required"])

    def test_result_change_rebuilds_result_nodes_and_dependents(self):
        from omega_latex_t.delta import semantic_delta

        before = DocumentIR.from_mapping(FIXTURE)
        raw = json.loads(json.dumps(FIXTURE))
        raw["results"]["metric.value"] = "99%"
        after = DocumentIR.from_mapping(raw)
        delta = semantic_delta(before, after)
        self.assertTrue(delta["results_changed"])
        self.assertEqual(delta["results_changed_keys"], ["metric.value"])
        self.assertIn("result.x", delta["affected_after"])

    def test_structured_math_ir_renders_and_checks_units(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2] = {
            "id": "eq.energy",
            "kind": "equation",
            "content": "",
            "symbols": [
                {"symbol": "E", "meaning": "energy", "unit": "J"},
                {"symbol": "m", "meaning": "mass", "unit": "kg"},
                {"symbol": "c", "meaning": "speed", "unit": "m/s"},
            ],
            "math_ir": {
                "op": "eq",
                "lhs": {"op": "symbol", "name": "E"},
                "rhs": {
                    "op": "mul",
                    "args": [
                        {"op": "symbol", "name": "m"},
                        {
                            "op": "pow",
                            "base": {"op": "symbol", "name": "c"},
                            "exp": {"op": "number", "value": 2},
                        },
                    ],
                },
            },
        }
        raw["nodes"][3]["dependencies"] = ["eq.energy"]
        doc = DocumentIR.from_mapping(raw)
        report = audit_document(doc)
        self.assertTrue(report.passed)
        latex = DocumentCompiler().render(doc).latex
        self.assertIn("E =", latex)
        self.assertIn("c}^{2", latex)

    def test_structured_math_ir_detects_dimension_error(self):
        expr = {
            "op": "eq",
            "lhs": {"op": "symbol", "name": "E"},
            "rhs": {"op": "symbol", "name": "m"},
        }
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["math_ir"] = expr
        raw["nodes"][2]["symbols"] = [
            {"symbol": "E", "meaning": "energy", "unit": "J"},
            {"symbol": "m", "meaning": "mass", "unit": "kg"},
        ]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("MATH_DIMENSION_MISMATCH", {x.code for x in report.errors})

    def test_unit_algebra(self):
        self.assertEqual(parse_unit("J"), parse_unit("kg*m^2/s^2"))
        expr = {
            "op": "div",
            "left": {"op": "symbol", "name": "x"},
            "right": {"op": "symbol", "name": "t"},
        }
        dim = infer_dimension(expr, {"x": "m", "t": "s"})
        self.assertEqual(dim, parse_unit("m/s"))
        self.assertIn(r"\frac", render_math(expr))

    def test_notation_registry_and_rename_plan(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][1]["symbols"] = [{"symbol": "G", "meaning": "graph", "unit": "1"}]
        raw["nodes"][2]["symbols"] = [{"symbol": "G", "meaning": "generator", "unit": "1"}]
        doc = DocumentIR.from_mapping(raw)
        registry = notation_registry(doc)
        plan = notation_rename_plan(doc)
        self.assertEqual(registry["collision_count"], 1)
        self.assertTrue(plan["requires_review"])
        self.assertTrue(any(x["proposed_symbol"] != "G" for x in plan["proposals"]))

    def test_evidence_matrix_requires_explicit_review_marker_for_support(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][3]["status"] = "established"
        raw["nodes"][3]["sources"] = ["src.1"]
        doc = DocumentIR.from_mapping(raw)
        matrix = evidence_matrix(doc)
        row = next(x for x in matrix["rows"] if x["node_id"] == "claim.x")
        self.assertFalse(row["support_review_complete"])
        report = audit_document(doc)
        self.assertIn("SOURCE_SUPPORT_UNREVIEWED", {x.code for x in report.warnings})

    def test_depth_projection_adds_dependency_closure(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["min_depth"] = 4
        raw["nodes"][3]["min_depth"] = 1
        doc = DocumentIR.from_mapping(raw)
        projected = project_depth(doc, 1)
        ids = {x.id for x in projected.nodes}
        self.assertIn("claim.x", ids)
        self.assertIn("eq.x", ids)
        self.assertIn("eq.x", projected.provenance["depth_projection"]["dependency_promoted"])

    def test_rebuild_plan_is_sharded_and_checkpointed(self):
        before = DocumentIR.from_mapping(FIXTURE)
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["content"] = "x = changed"
        after = DocumentIR.from_mapping(raw)
        plan = rebuild_plan(before, after, shard_size=1)
        self.assertTrue(plan["rebuild_required"])
        self.assertGreaterEqual(len(plan["shards"]), 1)
        self.assertFalse(plan["checkpoint"]["complete"])

    def test_incremental_cache_hits_second_build(self):
        doc = DocumentIR.from_mapping(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / "cache"
            out1 = Path(td) / "out1"
            out2 = Path(td) / "out2"
            first = DocumentCompiler().build_incremental_to(doc, out1, cache)
            second = DocumentCompiler().build_incremental_to(doc, out2, cache)
            self.assertEqual(first.cache_receipt["hits"], 0)
            self.assertEqual(first.cache_receipt["misses"], len(doc.nodes))
            self.assertEqual(second.cache_receipt["hits"], len(doc.nodes))
            self.assertEqual(second.cache_receipt["misses"], 0)
            self.assertEqual(first.latex_hash, second.latex_hash)

    def test_theorem_bundle_separates_formal_stub_from_proof(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"].extend(
            [
                {
                    "id": "thm.energy",
                    "kind": "theorem",
                    "content": "Energy relation under explicit assumptions.",
                    "status": "proven",
                    "dependencies": ["def.x"],
                    "metadata": {
                        "formal_system": "lean",
                        "formal_statement": "True",
                        "formal_verified": False,
                        "numerical_test_contract": {"cases": 3},
                    },
                },
                {
                    "id": "proof.energy",
                    "kind": "proof",
                    "content": "Narrative proof.",
                    "dependencies": ["thm.energy"],
                },
            ]
        )
        doc = DocumentIR.from_mapping(raw)
        with tempfile.TemporaryDirectory() as td:
            paths = write_theorem_bundle(doc, "thm.energy", td)
            lean = paths["formal_stub"].read_text()
            manifest = json.loads(paths["manifest"].read_text())
            self.assertIn("sorry", lean)
            self.assertEqual(manifest["formal_status"], "stub-or-unverified")
            self.assertIn("never proof", json.loads(paths["theorem"].read_text())["boundary"])

    def test_depth_projection_preserves_proven_theorem_proof_obligation(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"].extend([
            {"id": "thm.depth", "kind": "theorem", "content": "Depth theorem.", "status": "proven", "dependencies": ["def.x"], "min_depth": 3},
            {"id": "proof.depth", "kind": "proof", "content": "Depth proof.", "dependencies": ["thm.depth"], "min_depth": 5},
        ])
        projected = project_depth(DocumentIR.from_mapping(raw), 3)
        ids = {node.id for node in projected.nodes}
        self.assertIn("thm.depth", ids)
        self.assertIn("proof.depth", ids)
        self.assertTrue(audit_document(projected).passed)

    def test_source_drift_rebuilds_claim_and_dependents(self):
        from omega_latex_t.delta import semantic_delta
        before = DocumentIR.from_mapping(FIXTURE)
        raw = json.loads(json.dumps(FIXTURE))
        raw["sources"][0]["sha256"] = "changed"
        after = DocumentIR.from_mapping(raw)
        delta = semantic_delta(before, after)
        self.assertTrue(delta["sources_changed"])
        self.assertIn("eq.x", delta["affected_after"])
        self.assertIn("result.x", delta["affected_after"])

    def test_exp_requires_dimensionless_argument(self):
        raw = json.loads(json.dumps(FIXTURE))
        raw["nodes"][2]["math_ir"] = {
            "op": "eq",
            "lhs": {"op": "number", "value": 1},
            "rhs": {"op": "func", "name": "exp", "args": [{"op": "symbol", "name": "x"}]},
        }
        raw["nodes"][2]["symbols"] = [{"symbol": "x", "meaning": "position", "unit": "m"}]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("MATH_DIMENSION_MISMATCH", {x.code for x in report.errors})

if __name__ == "__main__":
    unittest.main()
