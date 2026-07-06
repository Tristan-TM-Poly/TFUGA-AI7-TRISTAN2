from pathlib import Path

from omega_gov_qc_t.cli import main
from omega_gov_qc_t import GraphExporter, MunicipalReportBuilder


def test_municipal_report_builder_generates_artifacts():
    artifacts = MunicipalReportBuilder().build_demo()

    assert "Municipalite-OAK Demo Report" in artifacts.report_markdown
    assert "municipal_demo_bundle" in artifacts.bundle_json
    assert artifacts.metadata["oak_deployable"] is True
    assert len(artifacts.graph.nodes) >= 3


def test_graph_exporter_outputs_graphml():
    artifacts = MunicipalReportBuilder().build_demo()
    graphml = GraphExporter().to_graphml(artifacts.graph).content

    assert "<graphml" in graphml
    assert "Demo Municipality" in graphml
    assert "produces_review_signal" in graphml


def test_cli_demo_generates_all_artifacts(tmp_path: Path):
    out_dir = tmp_path / "generated"
    exit_code = main(["demo", "--out", str(out_dir)])

    assert exit_code == 0
    assert (out_dir / "municipal_demo_report.md").exists()
    assert (out_dir / "municipal_demo_bundle.json").exists()
    assert (out_dir / "municipal_demo.graphml").exists()


def test_cli_individual_outputs(tmp_path: Path):
    report_path = tmp_path / "report.md"
    bundle_path = tmp_path / "bundle.json"
    graph_path = tmp_path / "graph.graphml"

    assert main(["report", "--out", str(report_path)]) == 0
    assert main(["bundle", "--out", str(bundle_path)]) == 0
    assert main(["graphml", "--out", str(graph_path)]) == 0

    assert "Municipalite-OAK Demo Report" in report_path.read_text(encoding="utf-8")
    assert "municipal_demo_bundle" in bundle_path.read_text(encoding="utf-8")
    assert "<graphml" in graph_path.read_text(encoding="utf-8")
