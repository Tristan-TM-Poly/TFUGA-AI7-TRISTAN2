from pathlib import Path

from rosette_tristan.real_render import render_mathtext_png
from rosette_tristan.visual_oak import classify_visual_oak, combine_scores, run_visual_oak


def test_combine_scores_requires_source_crop_for_full_score():
    assert combine_scores(1.0, None) == 0.55
    assert combine_scores(1.0, 1.0) == 1.0


def test_classify_visual_oak():
    assert classify_visual_oak(1.0, has_source_crop=False) == "visual_rendered_no_source_crop"
    assert classify_visual_oak(0.95, has_source_crop=True) == "visual_match_not_certified"
    assert classify_visual_oak(0.80, has_source_crop=True) == "visual_review_needed"
    assert classify_visual_oak(0.20, has_source_crop=True) == "visual_mismatch"


def test_run_visual_oak_without_crop(tmp_path: Path):
    report = run_visual_oak("x=y", reference_latex="x=y", out_dir=tmp_path)
    assert report.oak_status == "visual_rendered_no_source_crop"
    assert report.visual_oak_score <= 0.55
    assert "visual_oak_missing_source_crop" in report.memory_minus
    assert (tmp_path / "real_render" / "E1_candidate.png").exists()


def test_run_visual_oak_with_matching_crop(tmp_path: Path):
    crop = tmp_path / "crop.png"
    render_mathtext_png("x=y", crop)
    report = run_visual_oak("x=y", reference_latex="x=y", source_crop_png=crop, out_dir=tmp_path, equation_id="E1")
    assert report.oak_status == "visual_match_not_certified"
    assert report.visual_oak_score >= 0.92
    assert report.source_crop_compare is not None
    assert (tmp_path / "source_crop" / "E1_candidate.png").exists()
