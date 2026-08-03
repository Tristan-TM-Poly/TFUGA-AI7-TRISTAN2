from __future__ import annotations

import json
from pathlib import Path

from qc_scipatent_digest.cli import main
from qc_scipatent_digest.entity_resolution import cluster_people, entity_warnings, normalize_entity
from qc_scipatent_digest.pipeline import DigestPipeline


def test_plus_ultra_pipeline_outputs(tmp_path: Path) -> None:
    result = DigestPipeline().run(tmp_path)
    assert result.documents == 6
    assert result.opportunities == 6
    assert result.bridges == 9
    for relative in [
        "pipeline_summary.json",
        "documents.json",
        "opportunities.json",
        "entity_clusters.json",
        "release_assessment.md",
        "reuse_blueprints.md",
        "canon_pack/dct_cards.md",
        "digest.sqlite",
    ]:
        assert (tmp_path / relative).exists(), relative
    payload = json.loads((tmp_path / "pipeline_summary.json").read_text(encoding="utf-8"))
    assert payload["documents"] == 6
    assert payload["opportunities"] == 6
    assert payload["bridges"] == 9


def test_cli_plus_ultra(tmp_path: Path) -> None:
    out = tmp_path / "cli"
    assert main(["plus-ultra", "--out", str(out)]) == 0
    assert (out / "pipeline_summary.json").exists()


def test_entity_resolution_warning() -> None:
    assert normalize_entity("Polytechnique Montréal") == "polytechnique montr al"
    clusters = cluster_people(["A. Researcher", "B. Researcher", "C. Other"])
    warnings = entity_warnings(clusters)
    assert any(item.startswith("review_cluster:researcher") for item in warnings)
