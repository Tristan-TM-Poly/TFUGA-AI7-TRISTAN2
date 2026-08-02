from pathlib import Path
from omega_pct_t.pipeline import OmegaPCTPipeline

catalog = Path(__file__).parents[1] / "data" / "omega_pct_catalog.json"
report = OmegaPCTPipeline.from_catalog(catalog).run_qed_reference(
    Path("generated/omega_pct_t/demo"), count=128, sqrt_s=10.0, seed=7
)
print(report.combined_report["passed"], report.hypergraph_nodes, report.hypergraph_edges)
