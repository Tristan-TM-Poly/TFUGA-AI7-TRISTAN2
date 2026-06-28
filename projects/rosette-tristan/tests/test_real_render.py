import json
from pathlib import Path

from rosette_tristan.real_render import image_similarity, real_render_diff, render_mathtext_png


def test_render_mathtext_png_creates_file(tmp_path: Path):
    out = tmp_path / "eq.png"
    render_mathtext_png(r"\frac{dx}{dt}=-kx+u(t)", out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_image_similarity_for_identical_render(tmp_path: Path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    latex = r"x=y"
    render_mathtext_png(latex, a)
    render_mathtext_png(latex, b)
    assert image_similarity(a, b) >= 0.99


def test_real_render_diff_outputs_report(tmp_path: Path):
    result = real_render_diff(r"\frac{dx}{dt} = -k x + u(t)", reference=r"\frac{dx}{dt}=-kx+u(t)", out_dir=tmp_path, equation_id="E1")
    assert result.oak_status in {"render_usable_not_certified", "render_review_needed"}
    assert result.candidate_png is not None
    assert Path(result.candidate_png).exists()
    assert result.reference_png is not None
    assert Path(result.reference_png).exists()
    payload = result.to_dict()
    assert payload["render_backend"] == "matplotlib_mathtext"


def test_real_render_report_json_roundtrip(tmp_path: Path):
    result = real_render_diff("x=y", reference="x=y", out_dir=tmp_path)
    report = tmp_path / "report.json"
    report.write_text(json.dumps(result.to_dict()), encoding="utf-8")
    loaded = json.loads(report.read_text(encoding="utf-8"))
    assert loaded["image_score"] >= 0.99
