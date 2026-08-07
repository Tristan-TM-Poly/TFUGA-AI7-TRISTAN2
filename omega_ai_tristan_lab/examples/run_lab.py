"""Example run for Ω-AI-TRISTAN-LAB."""

from __future__ import annotations

from dataclasses import asdict
from pprint import pprint

from omega_ai_tristan_lab import AgentHarness


if __name__ == "__main__":
    idea = "Agent IA qui lit des PDFs, les traduit en LaTeX, code, tests et rapport OAK."
    report = AgentHarness().run(idea)
    pprint({
        "theory_card": asdict(report["theory_card"]),
        "oak_report": asdict(report["oak_report"]),
        "bayes_decision": report["bayes_decision"],
        "ip_classification": asdict(report["ip_classification"]),
        "revenue_paths": [asdict(path) for path in report["revenue_paths"]],
    })
