"""Built-in TristanLab plugin exposed through the shared runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .agent_harness import AgentHarness
from .capabilities import CapabilitySpec


class OmegaAITristanLabPlugin:
    name = "omega-ai-tristan-lab"
    version = "0.7.0"

    def capabilities(self) -> Sequence[str]:
        return ("idea-report", "analyze")

    def capability_specs(self) -> Sequence[CapabilitySpec]:
        return (
            CapabilitySpec(
                id="tristan.idea.analyze",
                task="idea-report",
                description="Transform an idea into structured OAK/Bayes/IP/revenue evidence.",
                input_kind="idea",
                output_kind="analysis-report",
                permissions=("PURE",),
                deterministic=True,
                tags=("oak", "theory", "analysis"),
            ),
        )

    def run(self, task: str, payload: Mapping[str, Any]) -> Any:
        if task not in {"idea-report", "analyze"}:
            raise KeyError(f"Unsupported task {task!r}. Supported tasks: idea-report, analyze")
        idea = str(payload.get("idea", "")).strip()
        if not idea:
            raise ValueError("payload['idea'] is required")
        return AgentHarness().run(idea)


plugin = OmegaAITristanLabPlugin()
