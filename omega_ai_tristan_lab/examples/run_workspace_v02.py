"""v0.2 workspace example for Ω-AI-TRISTAN-LAB."""

from __future__ import annotations

from pathlib import Path

from omega_ai_tristan_lab import Workspace


if __name__ == "__main__":
    root = Path("omega_runs")
    workspace = Workspace(root)
    run = workspace.run_with_documents(
        idea="Construire un agent OAK-safe qui transforme mes notes en prototypes, IP et revenus.",
        document_paths=["README.md", "omega_ai_manifesto.md"],
        context_query="OAK prototype IP revenue",
    )
    print(f"Run saved under: {run.run_dir}")
    print(f"JSON report: {run.json_report}")
    print(f"Markdown report: {run.markdown_report}")
