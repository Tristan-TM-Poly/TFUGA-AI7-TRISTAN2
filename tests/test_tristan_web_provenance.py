"""Tests for Tristan Web OS provenance and its explicit unresolved debt."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data"
AUDIT = ROOT / "scripts" / "audit_tristan_web_provenance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_tristan_web_provenance", AUDIT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def manifest():
    return json.loads((DATA / "provenance.json").read_text(encoding="utf-8"))


def test_provenance_audit_has_no_blocking_error() -> None:
    report = load_module().audit()
    assert not report["errors"], report["errors"]
    assert report["status"] in {"pass", "pass-with-debt"}
    assert report["metrics"]["theories"] == 44
    assert report["metrics"]["claims"] == 133


def test_unresolved_references_remain_explicit_debt() -> None:
    payload = manifest()
    unresolved = [item for item in payload["sources"] if item["status"] == "unresolved"]
    assert len(unresolved) == payload["metrics"]["unresolved"]
    assert unresolved, "The current catalog is expected to expose unresolved documentary debt"
    for source in unresolved:
        assert source["sha256"] is None
        assert source["size_bytes"] is None
        boundary = source["epistemic_boundary"].lower()
        assert "certify" in boundary
        assert "does not" in boundary or "do not" in boundary


def test_resolved_files_have_matching_hash_shape() -> None:
    payload = manifest()
    resolved = [item for item in payload["sources"] if item["status"] == "resolved-file"]
    assert len(resolved) == payload["metrics"]["resolved_files"]
    for source in resolved:
        assert len(source["sha256"]) == 64
        assert all(character in "0123456789abcdef" for character in source["sha256"])
        assert source["size_bytes"] >= 0


def test_exact_provenance_coverage_and_no_auto_promotion() -> None:
    payload = manifest()
    theory_ids = {item["id"] for item in json.loads((DATA / "theories.json").read_text(encoding="utf-8"))["theories"]}
    claim_ids = {item["id"] for item in json.loads((DATA / "claims.json").read_text(encoding="utf-8"))["claims"]}
    assert {item["theory_id"] for item in payload["theory_provenance"]} == theory_ids
    assert {item["claim_id"] for item in payload["claim_provenance"]} == claim_ids
    assert all(item["automatic_promotion"] is False for item in payload["claim_provenance"])


def test_provenance_view_is_routed_cached_and_accessible() -> None:
    application = (SITE / "src" / "application.js").read_text(encoding="utf-8")
    html = (SITE / "index.html").read_text(encoding="utf-8")
    worker = (SITE / "sw.js").read_text(encoding="utf-8")
    view = (SITE / "src" / "views" / "provenance.js").read_text(encoding="utf-8")
    assert "provenance: renderProvenance" in application
    assert 'data-route="provenance"' in html
    assert "src/views/provenance.js" in worker
    assert "data/provenance.json" in worker
    assert 'sectionHeader("Info² / Provenance"' in view
    assert "SHA-256 ≠ preuve" in view


def test_provenance_contract_is_json_schema_2020_12() -> None:
    schema = json.loads((ROOT / "schemas" / "tristan_web_os" / "provenance.schema.json").read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["properties"]["hash_algorithm"]["const"] == "sha256"
    assert schema["properties"]["metrics"]["properties"]["theories"]["const"] == 44
    assert schema["properties"]["metrics"]["properties"]["claims"]["const"] == 133
