from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from omega_latex_t import DocumentCompiler, DocumentIR, audit_document


FIXTURE = {
    "meta": {"title": "Test", "author": "Omega", "language": "en"},
    "sources": [{"id": "src.1", "citation": "fixture"}],
    "results": {"metric.value": "12.5%"},
    "nodes": [
        {"id": "sec", "kind": "section", "title": "Core"},
        {"id": "def.x", "kind": "definition", "content": "An evidence-bound object.", "status": "draft"},
        {"id": "eq.x", "kind": "equation", "content": "x = y + z", "dependencies": ["def.x"], "sources": ["src.1"], "dimension_lhs": "L", "dimension_rhs": "L"},
        {"id": "claim.x", "kind": "claim", "content": "A bounded claim.", "dependencies": ["eq.x"], "status": "draft"},
        {"id": "result.x", "kind": "result", "content": "A measured value injected from the result registry.", "dependencies": ["claim.x"], "status": "draft", "result_key": "metric.value"}
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
        order = [x.id for x in DocumentCompiler().topological_nodes(DocumentIR.from_mapping(raw))]
        self.assertLess(order.index("def.x"), order.index("eq.x"))
        self.assertLess(order.index("eq.x"), order.index("claim.x"))

    def test_missing_dependency_fails_closed(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"][1]["dependencies"] = ["missing"]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertFalse(report.passed)
        self.assertIn("DOCIR_MISSING_DEPENDENCY", {x.code for x in report.errors})

    def test_cycle_is_detected(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"][1]["dependencies"] = ["claim.x"]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("DEPENDENCY_CYCLE", {x.code for x in report.errors})

    def test_dimension_mismatch(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"][2]["dimension_rhs"] = "T"
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("DIMENSION_MISMATCH", {x.code for x in report.errors})

    def test_symbol_collision_warning(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"][1]["symbols"] = [{"symbol": "G", "meaning": "graph"}]; raw["nodes"][2]["symbols"] = [{"symbol": "G", "meaning": "generator"}]
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertTrue(report.passed)
        self.assertIn("SYMBOL_COLLISION", {x.code for x in report.warnings})

    def test_proven_theorem_requires_proof(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"].append({"id": "thm", "kind": "theorem", "content": "A theorem.", "status": "proven", "dependencies": ["def.x"]})
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertIn("PROOF_MISSING", {x.code for x in report.errors})

    def test_proven_theorem_with_reverse_proof_link(self):
        raw = json.loads(json.dumps(FIXTURE)); raw["nodes"].extend([{"id": "thm", "kind": "theorem", "content": "A theorem.", "status": "proven", "dependencies": ["def.x"]}, {"id": "proof.thm", "kind": "proof", "content": "Proof body.", "dependencies": ["thm"]}])
        report = audit_document(DocumentIR.from_mapping(raw))
        self.assertNotIn("PROOF_MISSING", {x.code for x in report.errors})

    def test_build_writes_evidence_bundle(self):
        doc = DocumentIR.from_mapping(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            artifact = DocumentCompiler().build_to(doc, td)
            paths = {p.name for p in Path(td).iterdir()}
            self.assertTrue({"document.tex", "docir.json", "oak-report.json", "manifest.json", "m_minus.jsonl"} <= paths)
            manifest = json.loads((Path(td) / "manifest.json").read_text())
            self.assertEqual(manifest["semantic_hash"], artifact.semantic_hash)
            self.assertTrue(manifest["oak_passed"])


if __name__ == "__main__":
    unittest.main()
