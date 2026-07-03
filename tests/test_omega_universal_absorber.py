from __future__ import annotations

import json
import zipfile
from pathlib import Path

from omega_prof_poly_t.universal_absorber import absorb_path, render_graphml, write_outputs


def test_absorb_directory_builds_chunks_claims_and_oak_report(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "theory.md").write_text(
        "# Ω-CVCD-T\n\nTheory: compression/decompression creates a testable HGFM claim. "
        "OAK requires evidence, residue tracking, and no proof without validation.",
        encoding="utf-8",
    )

    result = absorb_path(corpus)

    assert result.oak_report["status"] == "dry_run_only"
    assert result.oak_report["source_objects"] == 1
    assert result.chunks
    assert result.claims
    assert result.hyperedges
    assert result.oak_report["publishable"] is False


def test_absorb_zip_preserves_container_and_writes_outputs(tmp_path: Path) -> None:
    zip_path = tmp_path / "theories.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("notes/claim.txt", "Hypothesis: HGFM links claims to evidence and prototypes.")
        archive.writestr("code/demo.py", "def demo():\n    return 'prototype'\n")

    result = absorb_path(zip_path)
    out = tmp_path / "out"
    files = write_outputs(result, out)

    assert result.oak_report["source_objects"] == 2
    assert Path(files["manifest"]).exists()
    assert Path(files["graphml"]).read_text(encoding="utf-8").startswith("<?xml")
    payload = json.loads(Path(files["hypergraph"]).read_text(encoding="utf-8"))
    assert payload["oak_report"]["chunks"] >= 1


def test_graphml_contains_claim_and_tag_nodes(tmp_path: Path) -> None:
    file_path = tmp_path / "claim.md"
    file_path.write_text("Claim: CVCD + OAK makes raw extraction falsifiable.", encoding="utf-8")
    result = absorb_path(file_path)
    graphml = render_graphml(result)

    assert "claim" in graphml
    assert "cvcd" in graphml.lower()
    assert "oak" in graphml.lower()
