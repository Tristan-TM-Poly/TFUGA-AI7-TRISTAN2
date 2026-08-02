"""Baseline deterministic checks shared by Tristan Web OS R0.2 and R0.3."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data" / "theories.json"

REQUIRED_THEORY_FIELDS = {
    "id", "symbol", "title", "summary", "domains", "maturity", "evidence",
    "artifacts", "oak", "status_note", "next_action", "source_path",
    "family", "claims_count", "version", "visibility", "risks", "publication", "links",
}
REQUIRED_OAK_FIELDS = {"verite", "utilite", "testabilite", "simplicite", "valeur", "protection"}
ALLOWED_MATURITY = {"hypothèse", "architecture", "prototype", "testé", "reproduit", "produit"}


def load_payload() -> dict[str, object]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_static_application_files_exist() -> None:
    required = (
        "index.html", "styles.css", "r03.css", "app.js", "README.md",
        "app.webmanifest", "sw.js", "src/application.js", "src/data-store.js",
    )
    for relative_path in required:
        path = SITE / relative_path
        assert path.is_file(), f"Missing public-site file: {relative_path}"
        assert path.stat().st_size > 20, f"Unexpectedly small file: {relative_path}"


def test_html_references_local_assets_and_accessibility_hooks() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html
    assert 'href="r03.css"' in html
    assert 'src="app.js"' in html
    assert 'type="module"' in html
    assert 'class="skip-link"' in html
    assert 'aria-live="polite"' in html
    assert 'id="global-search"' in html
    assert "OAK ∧ IP ∧ Privacy ∧ Security" in html


def test_public_atlas_has_unique_structured_theories() -> None:
    payload = load_payload()
    theories = payload["theories"]
    assert isinstance(theories, list)
    assert len(theories) == 44
    ids = [theory["id"] for theory in theories]
    assert len(ids) == len(set(ids)), "Theory ids must be unique"
    for theory in theories:
        assert REQUIRED_THEORY_FIELDS <= set(theory)
        assert theory["maturity"] in ALLOWED_MATURITY
        assert isinstance(theory["domains"], list) and theory["domains"]
        assert isinstance(theory["artifacts"], int) and theory["artifacts"] >= 0
        assert REQUIRED_OAK_FIELDS == set(theory["oak"])
        assert all(0.0 <= float(value) <= 1.0 for value in theory["oak"].values())
        assert str(theory["status_note"]).strip()
        assert str(theory["next_action"]).strip()
        assert theory["publication"]["automatic_external_action"] is False


def test_dataset_keeps_oak_disclaimer_and_negative_result() -> None:
    payload = load_payload()
    disclaimer = str(payload["disclaimer"]).lower()
    assert "oak" in disclaimer
    assert "provisoires" in disclaimer
    assert "certification" in disclaimer
    combined_status = " ".join(str(theory["status_note"]).lower() for theory in payload["theories"])
    assert "fwt standard" in combined_status
    assert "n’a pas battu" in combined_status or "n'a pas battu" in combined_status


def test_modular_javascript_uses_safe_dom_rendering() -> None:
    app = (SITE / "app.js").read_text(encoding="utf-8")
    application = (SITE / "src" / "application.js").read_text(encoding="utf-8")
    store = (SITE / "src" / "data-store.js").read_text(encoding="utf-8")
    ui = (SITE / "src" / "ui.js").read_text(encoding="utf-8")
    assert "startApplication" in app
    assert "CorpusStore" in application
    assert '"data/theories.json"' in store
    assert '"data/claims.json"' in store
    assert '"data/relations.json"' in store
    assert "textContent" in ui
    assert "Unsafe html option is forbidden" in ui
