import json
from pathlib import Path

from rosette_tristan.bench_runner import run_bench


def test_run_bench_outputs_report(tmp_path: Path):
    report = run_bench(tmp_path)
    assert report.oak_status == "bench_passed_not_certified"
    assert len(report.cases) == 3
    assert (tmp_path / "rosette_bench_report.json").exists()
    payload = json.loads((tmp_path / "rosette_bench_report.json").read_text(encoding="utf-8"))
    assert payload["suite"] == "rosette_minimal_oak_bench"
    assert "oak_honesty_score" in payload["aggregate_metrics"]


def test_run_bench_has_visual_case(tmp_path: Path):
    report = run_bench(tmp_path)
    cases = {case.name: case for case in report.cases}
    assert "visual_match" in cases
    assert cases["visual_match"].metrics["equation_render_score"] >= 0.92
