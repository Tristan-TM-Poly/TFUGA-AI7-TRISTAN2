import json
from pathlib import Path

import pytest

from rosette_tristan.real_render import render_mathtext_png
from rosette_tristan.source_crop_compare import compare_candidate_to_source_crop, parse_bbox


def test_parse_bbox_validates_shape():
    assert parse_bbox("1,2,3,4") == (1.0, 2.0, 3.0, 4.0)
    with pytest.raises(ValueError):
        parse_bbox("1,2,3")
    with pytest.raises(ValueError):
        parse_bbox("3,2,1,4")


def test_compare_candidate_to_matching_source_crop(tmp_path: Path):
    source = tmp_path / "source.png"
    latex = r"x=y"
    render_mathtext_png(latex, source)
    result = compare_candidate_to_source_crop(latex, source, out_dir=tmp_path, equation_id="E1")
    assert result.image_score >= 0.99
    assert result.oak_status == "source_crop_match_not_certified"
    assert result.candidate_png is not None
    assert Path(result.candidate_png).exists()


def test_compare_candidate_to_mismatching_source_crop(tmp_path: Path):
    source = tmp_path / "source.png"
    render_mathtext_png(r"a=b", source)
    result = compare_candidate_to_source_crop(r"x=y", source, out_dir=tmp_path, equation_id="E2")
    assert result.oak_status in {"source_crop_review_needed", "source_crop_mismatch"}
    assert result.memory_minus


def test_source_crop_report_roundtrip(tmp_path: Path):
    source = tmp_path / "source.png"
    render_mathtext_png(r"x=y", source)
    result = compare_candidate_to_source_crop(r"x=y", source, out_dir=tmp_path)
    report = tmp_path / "source_crop_compare_report.json"
    report.write_text(json.dumps(result.to_dict()), encoding="utf-8")
    loaded = json.loads(report.read_text(encoding="utf-8"))
    assert loaded["source_crop_png"].endswith("source.png")
