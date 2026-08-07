"""Built-in TristanLab plugin exposed through the shared runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .agent_harness import AgentHarness
from .capabilities import CapabilitySpec
from .schemas import SchemaSpec


class OmegaAITristanLabPlugin:
    name = "omega-ai-tristan-lab"
    distribution = "omega-ai-tristan-lab"
    version = "0.9.0"

    def capabilities(self) -> Sequence[str]:
        return ("idea-report", "analyze")

    def schema_specs(self) -> Sequence[SchemaSpec]:
        return (
            SchemaSpec(
                id="tristan.idea.v1",
                kind="mapping",
                required_keys=("idea",),
                optional_keys=(),
                allow_extra=True,
                description="Idea payload accepted by the built-in Tristan analysis capability.",
            ),
            SchemaSpec(
                id="tristan.analysis-report.v1",
                kind="mapping",
                required_keys=("oak_report",),
                allow_extra=True,
                description="Structured Tristan analysis report containing an OAK report.",
            ),
        )

    def capability_specs(self) -> Sequence[CapabilitySpec]:
        return (
            CapabilitySpec(
                id="tristan.idea.analyze",
                task="idea-report",
                description="Transform an idea into structured OAK/Bayes/IP/revenue evidence.",
                input_kind="idea",
                output_kind="analysis-report",
                input_schema="tristan.idea.v1",
                output_schema="tristan.analysis-report.v1",
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
