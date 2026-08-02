from pathlib import Path
import json
from omega_pct_t.pipeline import OmegaPCTPipeline

CATALOG = Path(__file__).parents[1] / "data" / "omega_pct_catalog.json"

def test_pipeline_writes_reproducible_artifacts(tmp_path):
    report = OmegaPCTPipeline.from_catalog(CATALOG).run_qed_reference(tmp_path, count=16, sqrt_s=10.0, seed=3)
    assert report.combined_report["passed"]
    assert report.event_count == 16
    assert report.hypergraph_nodes > 50
    for path in report.outputs.values():
        assert Path(path).exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["hypergraph_digest"] == report.hypergraph_digest
