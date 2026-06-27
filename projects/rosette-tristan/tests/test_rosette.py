from pathlib import Path
from rosette_tristan import RosettePipeline


def test_compile_outputs(tmp_path: Path):
    result = RosettePipeline().compile("examples/sample_paper.txt", tmp_path)
    assert len(result.equations) == 1
    assert result.claims
    assert (tmp_path / "OAK_REPORT.md").exists()
    assert (tmp_path / "code" / "equations.py").exists()
