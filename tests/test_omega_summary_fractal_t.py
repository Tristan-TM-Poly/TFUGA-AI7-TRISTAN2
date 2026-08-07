from __future__ import annotations
import json
from pathlib import Path
from omega_summary_fractal_t.audit import duplicate_candidates,gap_analysis
from omega_summary_fractal_t.cli import main
from omega_summary_fractal_t.render import render_markdown,write_bundle,write_operational_views
from omega_summary_fractal_t.scanner import RepositoryScanner,first_summary_line
from omega_summary_fractal_t.summarizer import SummaryEngine

def fixture_repo(tmp_path:Path)->Path:
 root=tmp_path/"demo";root.mkdir();(root/"README.md").write_text("# Demo\n\nCorpus root.\n",encoding="utf-8");system=root/"omega_alpha_t";system.mkdir();(system/"README.md").write_text("# Ω-ALPHA-T\n\nAlpha deterministic engine.\n",encoding="utf-8");(system/"__init__.py").write_text('"""Alpha package."""\n',encoding="utf-8");(system/"core.py").write_text('def solve(x: int) -> int:\n    """Return x plus one."""\n    return x + 1\n',encoding="utf-8");tests=root/"tests";tests.mkdir();(tests/"test_alpha.py").write_text("def test_alpha():\n    assert 2 == 2\n",encoding="utf-8");schemas=system/"schemas";schemas.mkdir();(schemas/"alpha.schema.json").write_text('{"type":"object"}\n',encoding="utf-8");concept=root/"omega_beta_t";concept.mkdir();(concept/"README.md").write_text("# Ω-BETA-T\n\nBeta concept only.\n",encoding="utf-8");return root

def test_first_summary_line_skips_heading():assert first_summary_line("# Title\n\nUseful sentence.","x")=="Useful sentence."
def test_scanner_detects_systems_and_symbols(tmp_path):
 scan=RepositoryScanner(fixture_repo(tmp_path)).scan(include_symbols=True);systems={n.path:n for n in scan.nodes if n.kind=="system"};assert {"omega_alpha_t","omega_beta_t"}<=set(systems);assert systems["omega_alpha_t"].status=="implemented";assert systems["omega_beta_t"].status=="documented";assert any(n.kind=="function" and n.title=="solve" for n in scan.nodes)
def test_depth_is_monotonic(tmp_path):
 e=SummaryEngine(fixture_repo(tmp_path));counts=[len(e.generate(depth=d).nodes) for d in range(7)];assert counts==sorted(counts);assert counts[0]==1;assert counts[-1]>counts[0]
def test_focus_selects_system(tmp_path):
 b=SummaryEngine(fixture_repo(tmp_path)).generate(depth=6,focus="alpha");paths={n.path for n in b.nodes};assert "omega_alpha_t" in paths;assert not any(p.startswith("omega_beta_t") for p in paths)
def test_gap_analysis_flags_documented_without_code(tmp_path):
 gaps=gap_analysis(RepositoryScanner(fixture_repo(tmp_path)).scan().nodes);assert any(g["system"]=="omega_beta_t" and g["kind"]=="documented_without_code" for g in gaps)
def test_bundle_fingerprint_is_deterministic(tmp_path,monkeypatch):
 root=fixture_repo(tmp_path);monkeypatch.setenv("SOURCE_DATE_EPOCH","1785795360");a=SummaryEngine(root).generate(depth=6);b=SummaryEngine(root).generate(depth=6);assert a.to_dict()==b.to_dict()
def test_fingerprint_changes_with_content(tmp_path):
 root=fixture_repo(tmp_path);e=SummaryEngine(root);a=e.generate(depth=3).cache_fingerprint;(root/"omega_alpha_t"/"core.py").write_text("def changed():\n    return 42\n",encoding="utf-8");assert a!=e.generate(depth=3).cache_fingerprint
def test_markdown_contains_oak_boundary(tmp_path):
 text=render_markdown(SummaryEngine(fixture_repo(tmp_path)).generate(depth=4,audience="oak"));assert "Limite épistémique" in text;assert "validation scientifique" in text
def test_write_bundle_and_operational_views(tmp_path):
 b=SummaryEngine(fixture_repo(tmp_path)).generate(depth=9);out=tmp_path/"out";g=write_bundle(b,out);g.update(write_operational_views(b,out));assert all(p.exists() for p in g.values());assert json.loads((out/"summary_d9_tristan.json").read_text())["schema_version"]=="1.0.0"
def test_all_depths_cli(tmp_path,monkeypatch):
 root=fixture_repo(tmp_path);out=tmp_path/"summaries";monkeypatch.setenv("SOURCE_DATE_EPOCH","1785795360");assert main(["all-depths",str(root),"--output-dir",str(out)])==0;assert len(json.loads((out/"depth_index.json").read_text()))==10;assert (out/"SUMMARY.md").exists()
def test_audit_cli_is_non_blocking_by_default(tmp_path):
 root=fixture_repo(tmp_path);assert main(["audit",str(root)])==0;assert main(["audit",str(root),"--fail-on-gap"])==2
def test_duplicate_detector_requires_review():
 from omega_summary_fractal_t.models import SummaryNode
 nodes=[SummaryNode("a","system","omega_alpha_t","Alpha Engine","signal analysis engine"),SummaryNode("b","system","omega_alpha_copy_t","Alpha Engine Copy","signal analysis engine")];found=duplicate_candidates(nodes,threshold=0.3);assert found;assert found[0]["status"]=="review_required"
