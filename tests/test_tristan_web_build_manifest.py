"""Byte-level regression tests for the Tristan Web OS build manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
MANIFEST_PATH = SITE / "data" / "build-manifest.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_has_stable_contract_and_boundary() -> None:
    payload = manifest()
    assert payload["schema_version"] == "0.3.0"
    assert payload["algorithm"] == "sha256(path\\0sha256\\0size\\n)"
    assert len(payload["root_sha256"]) == 64
    assert "does not certify" in payload["epistemic_boundary"]
    assert payload["metrics"]["files"] == len(payload["files"])
    assert payload["metrics"]["files"] >= 34


def test_every_manifest_file_exists_and_matches_hash_and_size() -> None:
    payload = manifest()
    paths = []
    for item in payload["files"]:
        relative = item["path"]
        paths.append(relative)
        path = SITE / relative
        assert path.is_file(), relative
        assert path.stat().st_size == item["size_bytes"], relative
        assert digest(path) == item["sha256"], relative
    assert len(paths) == len(set(paths))
    assert "data/build-manifest.json" not in paths


def test_root_hash_recomputes_from_sorted_records() -> None:
    payload = manifest()
    root = hashlib.sha256()
    records = sorted(payload["files"], key=lambda item: item["path"])
    for item in records:
        root.update(item["path"].encode("utf-8"))
        root.update(b"\0")
        root.update(item["sha256"].encode("ascii"))
        root.update(b"\0")
        root.update(str(item["size_bytes"]).encode("ascii"))
        root.update(b"\n")
    assert root.hexdigest() == payload["root_sha256"]


def test_manifest_covers_critical_application_assets() -> None:
    payload = manifest()
    paths = {item["path"] for item in payload["files"]}
    required = {
        "index.html",
        "app.js",
        "sw.js",
        "app.webmanifest",
        "src/application.js",
        "src/data-store.js",
        "src/oak-engine.js",
        "src/views/oakgate.js",
        "src/views/provenance.js",
        "data/theories.json",
        "data/claims.json",
        "data/relations.json",
        "data/provenance.json",
    }
    assert required <= paths


def test_build_manifest_is_cached_and_visible_in_provenance() -> None:
    worker = (SITE / "sw.js").read_text(encoding="utf-8")
    provenance = (SITE / "src" / "views" / "provenance.js").read_text(encoding="utf-8")
    assert "data/build-manifest.json" in worker
    assert 'loadJson("data/build-manifest.json", "files")' in provenance
    assert "Intégrité du snapshot public" in provenance
    assert "SHA-256 ≠ preuve" in provenance


def test_build_manifest_is_not_a_security_certificate() -> None:
    payload = manifest()
    boundary = payload["epistemic_boundary"].lower()
    for term in ["security", "scientific validity", "accessibility"]:
        assert term in boundary
