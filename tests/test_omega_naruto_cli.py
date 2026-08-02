import json

from omega_naruto_hmagfm.cli import build_report, main


def test_cli_report_exposes_oak_benchmark_gates_and_mminus() -> None:
    report = build_report()

    assert report["schema"] == "omega_naruto_hmagfm.report.v1.1"
    assert report["accepted"]["claim_id"] == "SUPPORTED"
    assert report["benchmark"]["oak_merge_correct"] is True
    assert report["benchmark"]["majority_vote_correct"] is False
    assert report["benchmark"]["highest_confidence_correct"] is False
    assert report["publication_gate"]["decision"] == "WARN"
    assert report["publication_gate"]["release_allowed"] is False
    assert len(report["mminus"]["entries"]) == 2


def test_cli_writes_deterministic_json(tmp_path, capsys) -> None:
    output = tmp_path / "omega_naruto_report.json"

    assert main(("--output", str(output))) == 0
    stdout = capsys.readouterr().out
    from_stdout = json.loads(stdout)
    from_file = json.loads(output.read_text(encoding="utf-8"))

    assert from_stdout == from_file
    assert from_file["accepted"]["claim_id"] == "SUPPORTED"
