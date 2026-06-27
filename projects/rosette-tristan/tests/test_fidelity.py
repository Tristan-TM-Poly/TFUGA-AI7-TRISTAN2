import json
from pathlib import Path

from rosette_tristan.fidelity_pipeline import RosetteFidelityPipeline


def test_fidelity_compile_outputs(tmp_path: Path):
    out = tmp_path / "out"
    result = RosetteFidelityPipeline().compile("examples/sample_paper.txt", out)
    assert len(result.equations) == 1
    assert result.claims
    assert (out / "source_refs.json").exists()
    assert (out / "fidelity_report.json").exists()
    assert (out / "theory_capsule.yaml").exists()


def test_page_markers_are_preserved(tmp_path: Path):
    paper = tmp_path / "paged.txt"
    paper.write_text(
        "---PAGE 1---\n# Title\n\nWe propose a claim.\n\n---PAGE 2---\nMath:\n\n$$x=y$$\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = RosetteFidelityPipeline().compile(paper, out)
    assert {block.source.page for block in result.blocks} == {1, 2}
    assert result.equations[0].source.page == 2
    refs = json.loads((out / "source_refs.json").read_text(encoding="utf-8"))
    assert any(ref["page"] == 2 for ref in refs)
    report = json.loads((out / "fidelity_report.json").read_text(encoding="utf-8"))
    assert report["counts"]["source_refs_with_page"] >= 2
