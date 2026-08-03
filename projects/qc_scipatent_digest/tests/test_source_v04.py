from pathlib import Path

from qc_scipatent_digest.cli import fixture_documents
from qc_scipatent_digest.pipeline import run_pipeline, science_ip_bridges


def test_fixture_pipeline_generates_plus_ultra_outputs(tmp_path: Path) -> None:
    docs = fixture_documents()
    summary = run_pipeline(docs, tmp_path)
    assert summary["documents"] == 6
    assert summary["opportunities"] >= 3
    assert summary["bridges"] >= 3
    assert (tmp_path / "PLUS_ULTRA_REPORT.md").exists()
    assert (tmp_path / "release_assessment.json").exists()


def test_science_ip_bridges_keep_oak_warning() -> None:
    bridges = science_ip_bridges(fixture_documents())
    assert bridges
    assert all("candidate bridge" in b["oak_warning"] for b in bridges)
