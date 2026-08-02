"""Deterministic checks for Tristan Web OS R0.1."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data" / "theories.json"


REQUIRED_THEORY_FIELDS = {
    "id",
    "symbol",
    "title",
    "summary",
    "domains",
    "maturity",
    "evidence",
    "artifacts",
    "oak",
    "status_note",
    "next_action",
    "source_path",
}

REQUIRED_OAK_FIELDS = {
    "verite",
    "utilite",
    "testabilite",
    "simplicite",
    "valeur",
    "protection",
}

ALLOWED_MATURITY = {"hypothèse", "architecture", "prototype"}


def load_payload() -> dict[str, object]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_static_site_files_exist() -> None:
    for relative_path in ("index.html", "styles.css", "app.js", "README.md"):
        path = SITE / relative_path
        assert path.is_file(), f"Missing public-site file: {relative_path}"
        assert path.stat().st_size > 100, f"Unexpectedly small file: {relative_path}"


def test_html_references_local_assets_and_accessibility_hooks() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html
    assert 'src="app.js"' in html
    assert 'class="skip-link"' in html
    assert 'aria-live="polite"' in html
    assert "OAKGate ∧ IPGate ∧ PrivacyGate ∧ SecurityGate" in html


def test_public_atlas_has_unique_structured_theories() -> None:
    payload = load_payload()
    theories = payload["theories"]
    assert isinstance(theories, list)
    assert len(theories) >= 8

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


def test_dataset_keeps_oak_disclaimer_and_negative_result() -> None:
    payload = load_payload()
    disclaimer = str(payload["disclaimer"]).lower()
    assert "provisoires" in disclaimer
    assert "preuve scientifique" in disclaimer

    combined_status = " ".join(
        str(theory["status_note"]).lower() for theory in payload["theories"]
    )
    assert "fwt standard" in combined_status
    assert "surpassé" in combined_status


def test_javascript_uses_text_content_for_dataset_rendering() -> None:
    javascript = (SITE / "app.js").read_text(encoding="utf-8")
    assert ".textContent" in javascript
    assert 'fetch("data/theories.json"' in javascript
    assert "renderOakBars" in javascript
