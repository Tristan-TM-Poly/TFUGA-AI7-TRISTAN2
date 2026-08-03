import json,os
from pathlib import Path
import pytest
from omega_synergy_n_t.ledger import ProofLedger
from omega_synergy_n_t.reporting import write_bundle,audit_bundle
from omega_synergy_n_t.cli import main
from omega_synergy_n_t.adapters import signatures_from_creation_dna


def test_ledger_roundtrip(tmp_path):
    l=ProofLedger(tmp_path/"l.jsonl"); l.append("measurement",{"x":1}); l.append("interaction",{"x":2}); assert l.verify()==(True,[])
def test_ledger_tamper(tmp_path):
    p=tmp_path/"l.jsonl"; l=ProofLedger(p); l.append("x",{"v":1}); p.write_text(p.read_text().replace('"v": 1','"v": 2')); assert not l.verify()[0]
def test_bundle_audit(tmp_path,monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH","123"); m=write_bundle(tmp_path,{"a.json":{"x":1}}); assert audit_bundle(tmp_path)["valid"] and m["generated_epoch"]==123
def test_bundle_tamper(tmp_path):
    write_bundle(tmp_path,{"a.json":{"x":1}}); (tmp_path/"a.json").write_text("{}\n"); assert not audit_bundle(tmp_path)["valid"]
def test_demo_cli(tmp_path): assert main(["demo","--fixture","pure_triplet","--output-dir",str(tmp_path)])==0 and (tmp_path/"manifest.json").exists()
def test_audit_cli(tmp_path,capsys):
    write_bundle(tmp_path,{"a.json":{"x":1}}); assert main(["audit","--bundle-dir",str(tmp_path)])==0; assert json.loads(capsys.readouterr().out)["valid"]
def test_experiment_cli(capsys): assert main(["experiment","A","B"])==0 and json.loads(capsys.readouterr().out)["design_type"]=="full_factorial"
def test_oak_cli(tmp_path,capsys):
    p=tmp_path/"c.json"; p.write_text("{}"); assert main(["oak","--candidate",str(p)])==0; assert json.loads(capsys.readouterr().out)["status"]=="BLOCKED"
def test_decompose_cli(tmp_path,capsys):
    out=tmp_path/"demo"; main(["demo","--fixture","pure_triplet","--output-dir",str(out)]); capsys.readouterr(); assert main(["decompose","--input",str(out/"measurements.json")])==0; assert len(json.loads(capsys.readouterr().out))==7
def test_spectrum_cli(tmp_path,capsys):
    out=tmp_path/"demo"; main(["demo","--fixture","pure_triplet","--output-dir",str(out)]); capsys.readouterr(); main(["spectrum","--input",str(out/"measurements.json")]); assert json.loads(capsys.readouterr().out)["dominant_order"]==3
def test_adapter():
    records=[{"name":"A","capabilities":[{"output_types":["x"]}],"needs":[],"domains":["d"],"evidence":[{"strength":.5}],"risks":{"r":.2}}]; assert signatures_from_creation_dna(records)["A"]["outputs"]==["x"]
def test_search_cli(tmp_path,capsys):
    p=tmp_path/"dna.json"; p.write_text(json.dumps([{"name":"A","capabilities":[{"output_types":["x"]}],"needs":[]},{"name":"B","capabilities":[],"needs":[{"input_types":["x"]}]}])); assert main(["search","--creation-dna",str(p),"--max-order","2"])==0; assert "2" in json.loads(capsys.readouterr().out)
