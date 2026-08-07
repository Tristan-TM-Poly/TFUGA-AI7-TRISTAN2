"""Built-in TristanLab plugin exposed through the shared runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .agent_harness import AgentHarness


class OmegaAITristanLabPlugin:
    name = "omega-ai-tristan-lab"
    version = "0.3.0"

    def capabilities(self) -> Sequence[str]:
        return ("idea-report", "oak-evaluate", "ip-map", "revenue-map")

    def run(self, task: str, payload: Mapping[str, Any]) -> Any:
        if task not in {"idea-report", "analyze"}:
            raise KeyError(
                f"Unsupported task {task!r}. Supported tasks: idea-report, analyze"
            )
        idea = str(payload.get("idea", "")).strip()
        if not idea:
            raise ValueError("payload['idea'] is required")
        return AgentHarness().run(idea)


plugin = OmegaAITristanLabPlugin()
