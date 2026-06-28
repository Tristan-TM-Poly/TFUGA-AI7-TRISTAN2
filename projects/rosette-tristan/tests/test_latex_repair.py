from pathlib import Path
import json

from rosette_tristan.latex_repair import normalize_latex, render_diff_repair


def test_normalize_latex_removes_layout_noise():
    assert normalize_latex(r"\left( x + y \right)") == "(x+y)"


def test_render_diff_repair_scores_reference_match():
    result = render_diff_repair(r"\frac{dx}{dt} = -k x + u(t)", reference=r"\frac{dx}{dt}=-kx+u(t)", equation_id="E1")
    assert result.symbol_score >= 0.85
    assert result.oak_status == "usable_not_certified"


def test_render_diff_repair_records_low_similarity():
    result = render_diff_repair("x = y", reference="a = b", equation_id="E2")
    assert result.oak_status == "repair_needed"
    assert "low_symbol_similarity_after_repair" in result.memory_minus


def test_render_diff_repair_can_write_payload(tmp_path: Path):
    result = render_diff_repair("x = y", reference="x=y")
    out = tmp_path / "render.json"
    out.write_text(json.dumps(result.to_dict()), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["equation_id"] == "E1"
