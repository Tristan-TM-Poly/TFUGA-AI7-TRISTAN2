import json
from xml.etree import ElementTree

from omega_naruto_hmagfm.cli import build_report, main


def test_cli_report_exposes_oak_benchmark_gates_graph_and_mminus() -> None:
    report = build_report()

    assert report["schema"] == "omega_naruto_hmagfm.report.v1.2"
    assert report["accepted"]["claim_id"] == "SUPPORTED"
    assert report["benchmark"]["oak_merge_correct"] is True
    assert report["benchmark"]["majority_vote_correct"] is False
    assert report["benchmark"]["highest_confidence_correct"] is False
    assert report["publication_gate"]["decision"] == "WARN"
    assert report["publication_gate"]["release_allowed"] is False
    assert report["robustness"]["base_winner_id"] == "SUPPORTED"
    assert report["robustness"]["stable_fraction"] == 0.8
    assert report["hgfmn_graph"]["schema"] == "omega_naruto_hgfmn.graph.v1"
    assert len(report["hgfmn_graph"]["nodes"]) >= 8
    assert len(report["mminus"]["entries"]) == 2


def test_cli_writes_deterministic_json_and_graphml(tmp_path, capsys) -> None:
    output = tmp_path / "omega_naruto_report.json"
    graphml = tmp_path / "omega_naruto.graphml"

    assert (
        main(
            (
                "--output",
                str(output),
                "--graphml-output",
                str(graphml),
            )
        )
        == 0
    )
    stdout = capsys.readouterr().out
    from_stdout = json.loads(stdout)
    from_file = json.loads(output.read_text(encoding="utf-8"))

    assert from_stdout == from_file
    assert from_file["accepted"]["claim_id"] == "SUPPORTED"
    root = ElementTree.fromstring(graphml.read_text(encoding="utf-8"))
    assert root.tag.endswith("graphml")
