"""Regression tests for Tristan Web OS R0.3."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data"
AUDIT_PATH = ROOT / "scripts" / "audit_tristan_web_os_r03.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_tristan_web_os_r03", AUDIT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_r03_audit_passes_without_errors() -> None:
    module = load_audit_module()
    audit = module.run_audit()
    assert not audit.errors, "\n".join(f"{item.code}: {item.message}" for item in audit.errors)
    assert audit.metrics["theories"] == 44
    assert audit.metrics["claims"] == 133
    assert audit.metrics["relations"] == 268
    assert audit.metrics["automatic_external_actions"] == 0
    assert audit.metrics["automatic_claim_promotions"] == 0


def test_every_claim_is_falsifiable_or_explicitly_limited() -> None:
    claims = read("claims.json")["claims"]
    for claim in claims:
        assert len(claim["falsification_or_limit"].strip()) >= 15
        assert len(claim["next_test"].strip()) >= 15
        assert claim["counter_hypotheses"]
        assert claim["support"]
        assert claim["automatic_promotion"] is False


def test_relations_are_navigation_only_and_referentially_valid() -> None:
    theories = read("theories.json")["theories"]
    relations = read("relations.json")["relations"]
    ids = {item["id"] for item in theories}
    for relation in relations:
        assert relation["source"] in ids
        assert relation["target"] in ids
        assert relation["source"] != relation["target"]
        assert relation["public_scope"] == "navigation"
        assert relation["evidence_required"] is True
        assert 0 <= relation["strength"] <= 1


def test_all_public_theories_have_four_gates_and_negative_memory() -> None:
    theories = read("theories.json")["theories"]
    gate_keys = {"oak_gate", "ip_gate", "privacy_gate", "security_gate"}
    for theory in theories:
        publication = theory["publication"]
        assert gate_keys <= set(publication)
        assert publication["automatic_external_action"] is False
        assert theory["risks"]
        assert theory["status_note"].strip()
        assert theory["next_action"].strip()


def test_application_registers_all_public_views() -> None:
    app = (SITE / "src" / "application.js").read_text(encoding="utf-8")
    html = (SITE / "index.html").read_text(encoding="utf-8")
    routes = ["dashboard", "atlas", "theory", "claims", "claim", "graph", "evidence", "provenance", "oakgate", "mminus", "roadmap", "about"]
    for route in routes:
        assert f"{route}:" in app
    for route in ["dashboard", "atlas", "claims", "graph", "evidence", "provenance", "oakgate", "mminus", "roadmap", "about"]:
        assert f'data-route="{route}"' in html
    assert 'type="module"' in html
    assert 'id="global-search"' in html
    assert 'id="live-region"' in html
    assert 'href="oakgate.css"' in html


def test_offline_shell_covers_data_modules_and_labs() -> None:
    worker = (SITE / "sw.js").read_text(encoding="utf-8")
    for item in [
        "data/theories.json", "data/claims.json", "data/relations.json", "data/provenance.json",
        "src/application.js", "src/data-store.js", "src/oak-engine.js", "src/views/graph.js",
        "src/views/provenance.js", "src/views/oakgate.js", "oakgate.css",
    ]:
        assert item in worker
    assert "fetch(" in worker
    assert "caches.open" in worker


def test_machine_contracts_are_valid_json() -> None:
    schema_dir = ROOT / "schemas" / "tristan_web_os"
    for name in ["theory.schema.json", "claim.schema.json", "relation.schema.json", "provenance.schema.json"]:
        schema = json.loads((schema_dir / name).read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
        assert schema["type"] == "object"
        assert schema["required"]
        assert "$data" not in json.dumps(schema)


def test_exporters_do_not_send_network_requests() -> None:
    exporters = (SITE / "src" / "exporters.js").read_text(encoding="utf-8")
    assert "fetch(" not in exporters
    assert "XMLHttpRequest" not in exporters
    assert "navigator.sendBeacon" not in exporters
    assert "new Blob" in exporters


def test_global_search_uses_text_content_safe_primitives() -> None:
    ui = (SITE / "src" / "ui.js").read_text(encoding="utf-8")
    application = (SITE / "src" / "application.js").read_text(encoding="utf-8")
    assert "textContent" in ui
    assert "Unsafe html option is forbidden" in ui
    assert ".innerHTML" not in application


def test_oakgate_never_claims_certification_or_auto_promotion() -> None:
    engine = (SITE / "src" / "oak-engine.js").read_text(encoding="utf-8")
    view = (SITE / "src" / "views" / "oakgate.js").read_text(encoding="utf-8")
    assert 'automatic_promotion: false' in engine
    assert '"human-review-candidate"' in engine
    assert "ne certifie" in engine.lower()
    assert "Auditer sans certifier" in view
    assert "Exporter le paquet OAK JSON" in view
