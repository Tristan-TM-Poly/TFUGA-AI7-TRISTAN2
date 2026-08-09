from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from omega_latex_t import DocumentCompiler, DocumentIR, Measurement, audit_document, attach_bibliography, bibliography_report, build_universe, metadocument_graph, parse_bibtex, propagate_independent, render_figure_ir, statement_sha256, theorem_bundle, universe_plan, verifier_receipt_report

BASE={"meta":{"title":"R08","author":"Omega","language":"en"},"sources":[{"id":"src.base","citation":"Base reference","locator":"p. 1"}],"results":{"metric.x":{"value":12.5,"uncertainty":0.4,"unit":"m","method":"std","coverage":0.95}},"nodes":[{"id":"sec","kind":"section","title":"Core"},{"id":"claim","kind":"claim","content":"Bounded claim.","status":"established","sources":["src.base"],"source_locators":{"src.base":"p. 1, Eq. 2"},"metadata":{"support":[{"source":"src.base","relation":"supports","reviewed":True}]}},{"id":"fig","kind":"figure","title":"Graph","figure_ir":{"kind":"graph","caption":"Dependency graph","nodes":[{"id":"a","label":"A","x":0,"y":0},{"id":"b","label":"B","x":2,"y":0}],"edges":[{"source":"a","target":"b","label":"depends"}]}},{"id":"result","kind":"result","content":"Measured result.","status":"measured","result_key":"metric.x","dependencies":["claim"]}]}

class OmegaLatexR08Tests(unittest.TestCase):
    def test_bibtex_parser_and_attach(self):
        entries=parse_bibtex('@article{einstein1905, author={Albert Einstein}, title={Zur Elektrodynamik}, year={1905}, doi={10.1000/example}}'); self.assertEqual(entries[0].key,"einstein1905"); report=bibliography_report(attach_bibliography(DocumentIR.from_mapping(BASE),entries)); self.assertIn("einstein1905",{item["id"] for item in report["sources"]})
    def test_bibtex_rejects_macros_and_duplicate_key(self):
        with self.assertRaises(ValueError): parse_bibtex('@article{x, title="A" # "B"}')
        with self.assertRaises(ValueError): parse_bibtex('@article{x,title={A}} @book{x,title={B}}')
    def test_source_locator_is_claim_level(self):
        report=audit_document(DocumentIR.from_mapping(BASE)); self.assertNotIn("SOURCE_LOCATOR_MISSING",{item.code for item in report.warnings}); raw=json.loads(json.dumps(BASE)); raw["sources"][0]["locator"]=""; raw["nodes"][1]["source_locators"]={}; self.assertIn("SOURCE_LOCATOR_MISSING",{item.code for item in audit_document(DocumentIR.from_mapping(raw)).warnings})
    def test_orphan_source_locator_fails(self):
        raw=json.loads(json.dumps(BASE)); raw["nodes"][1]["source_locators"]["src.other"]="p. 2"; self.assertIn("SOURCE_LOCATOR_ORPHAN",{item.code for item in audit_document(DocumentIR.from_mapping(raw)).errors})
    def test_figure_ir_graph_and_plot(self):
        rendered=render_figure_ir(BASE["nodes"][2]["figure_ir"],node_id="fig"); self.assertIn(r"\begin{tikzpicture}",rendered); self.assertIn(r"\draw[->]",rendered); plot={"kind":"plot","x_label":"t","y_label":"y","series":[{"name":"s","x":[0,1,2],"y":[1,2,4],"mode":"line+markers"}]}; self.assertIn(r"\begin{axis}",render_figure_ir(plot,node_id="plot"));
        with self.assertRaises(ValueError): render_figure_ir({"kind":"graph","nodes":[{"id":"bad id"}],"edges":[]})
    def test_compiler_emits_new_sidecars(self):
        doc=DocumentIR.from_mapping(BASE)
        with tempfile.TemporaryDirectory() as td:
            artifact=DocumentCompiler().build_to(doc,td); self.assertTrue(artifact.audit.passed); latex=(Path(td)/"document.tex").read_text(); self.assertIn(r"\usepackage{tikz}",latex); self.assertIn(r"\cite[",latex); self.assertIn(r"\begin{thebibliography}",latex); self.assertIn(r"\pm",latex)
            for name in ("bibliography-report.json","figure-manifest.json","uncertainty-ledger.json","verifier-receipts.json"): self.assertTrue((Path(td)/name).is_file(),name)
    def test_uncertainty_propagation(self):
        total=propagate_independent("add",[Measurement(2.0,0.1,"m"),Measurement(3.0,0.2,"m")]); self.assertAlmostEqual(total.value,5.0); self.assertAlmostEqual(total.uncertainty,(0.1**2+0.2**2)**0.5); product=propagate_independent("mul",[Measurement(2,0.1,"m"),Measurement(3,0.2,"s")]); self.assertAlmostEqual(product.value,6.0); self.assertGreater(product.uncertainty,0)
    def test_invalid_structured_result_fails_audit(self):
        raw=json.loads(json.dumps(BASE)); raw["results"]["metric.x"]["uncertainty"]=-1; self.assertIn("RESULT_UNCERTAINTY_INVALID",{item.code for item in audit_document(DocumentIR.from_mapping(raw)).errors})
    def test_verifier_receipt_requires_exact_statement_hash(self):
        raw=json.loads(json.dumps(BASE)); raw["nodes"].extend([{"id":"thm","kind":"theorem","title":"Demo","content":"Narrative theorem.","status":"proven","metadata":{"formal_system":"lean","formal_statement":"True"}},{"id":"proof","kind":"proof","content":"Narrative proof.","dependencies":["thm"]}]); raw["provenance"]={"verifier_receipts":[{"system":"lean","theorem_id":"thm","statement_sha256":statement_sha256("True"),"status":"passed","verifier_version":"4.x","artifact_sha256":"a"*64,"run_id":"fixture"}]}; doc=DocumentIR.from_mapping(raw); self.assertEqual(verifier_receipt_report(doc)["verified_count"],1); self.assertEqual(theorem_bundle(doc,"thm")["formal_projection"]["status"],"verified-external-receipt"); raw["provenance"]["verifier_receipts"][0]["statement_sha256"]="b"*64; doc=DocumentIR.from_mapping(raw); self.assertEqual(verifier_receipt_report(doc)["verified_count"],0); self.assertNotEqual(theorem_bundle(doc,"thm")["formal_projection"]["status"],"verified-external-receipt")
    def test_bare_formal_verified_does_not_self_certify(self):
        raw=json.loads(json.dumps(BASE)); raw["nodes"].extend([{"id":"thm","kind":"theorem","content":"Narrative theorem.","status":"proven","metadata":{"formal_system":"lean","formal_statement":"True","formal_verified":True}},{"id":"proof","kind":"proof","content":"Narrative proof.","dependencies":["thm"]}]); bundle=theorem_bundle(DocumentIR.from_mapping(raw),"thm"); self.assertEqual(bundle["formal_projection"]["status"],"stub-or-unverified"); self.assertTrue(bundle["formal_projection"]["metadata_verified_flag_supplied"])
    def test_metadocument_candidates(self):
        first=DocumentIR.from_mapping({"meta":{"title":"A"},"nodes":[{"id":"c1","kind":"claim","content":"Same text","metadata":{"canonical_key":"claim.k"}},{"id":"orphan","kind":"paragraph","content":"alone"}]}); second=DocumentIR.from_mapping({"meta":{"title":"B"},"nodes":[{"id":"c2","kind":"claim","content":"Same text","metadata":{"canonical_key":"claim.k"}},{"id":"c3","kind":"claim","content":"Different text","metadata":{"canonical_key":"claim.k"}}]}); graph=metadocument_graph({"A":first,"B":second}); self.assertTrue(graph["duplicate_candidates"]); self.assertTrue(graph["conflict_candidates"]); self.assertIn("A:orphan",graph["orphan_candidates"])
    def test_universe_plan_has_no_fixed_document_ceiling(self):
        plan=universe_plan({"entries":[{"id":f"d{i}","kind":"docir","path":f"d{i}.json"} for i in range(257)],"depths":[0,1,2],"shard_size":64}); self.assertEqual(plan["job_count"],771); self.assertGreater(len(plan["shards"]),1)
    def test_universe_build_and_resume(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); (base/"doc.json").write_text(json.dumps(BASE)); manifest=base/"universe.json"; manifest.write_text(json.dumps({"entries":[{"id":"demo","kind":"docir","path":"doc.json"}],"depths":[0,1,3],"shard_size":2})); out=base/"out"; cache=base/"cache"; first=build_universe(manifest,out,cache); self.assertEqual(first["completed_job_count"],3); second=build_universe(manifest,out,cache,resume=True); self.assertTrue(all(item["status"]=="resumed-skip" for item in second["receipts"])); self.assertTrue((out/"demo"/"D3"/"document.tex").is_file())

if __name__=="__main__": unittest.main()
