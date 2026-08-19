from pathlib import Path

from omega_github_mycelium_t.intent import IntentCompiler
from omega_github_mycelium_t.orchestrator import MyceliumOrchestrator
from omega_github_mycelium_t.snapshot import SnapshotBundle


ROOT = Path(__file__).resolve().parents[1]
snapshot = SnapshotBundle.read(ROOT / "data/omega_github_mycelium_t/repository_snapshot_2026_08_03.json")
intent = IntentCompiler().compile(
    "Détecter automatiquement une divergence entre documentation et code.",
    root_creation="omega-doc-t",
    candidate_repositories=("Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",),
    observed_depth_target=9,
)
result = MyceliumOrchestrator().compile(
    intent,
    snapshot,
    ROOT / "generated/omega_github_mycelium_t/demo",
)
print(result)
