"""Compile and search schema-compatible capability pipelines."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import deque
from typing import Any, Iterable

from .capabilities import CapabilityGraph, CapabilityProvider
from .schemas import SchemaGraph


@dataclass(frozen=True, slots=True)
class CompiledStep:
    capability: str
    provider: str
    input_schema: str
    output_schema: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PipelinePlan:
    steps: tuple[CompiledStep, ...]
    initial_schema: str
    final_schema: str
    valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "initial_schema": self.initial_schema,
            "final_schema": self.final_schema,
            "valid": self.valid,
        }


class PipelineCompiler:
    def __init__(self, capabilities: CapabilityGraph, schemas: SchemaGraph):
        self.capabilities = capabilities
        self.schemas = schemas

    def compile(self, capability_ids: Iterable[str], *, initial_schema: str = "tristan.any") -> PipelinePlan:
        current = initial_schema
        steps: list[CompiledStep] = []
        for capability_id in capability_ids:
            provider = self.capabilities.resolve(capability_id)
            spec = provider.capability
            input_schema = spec.input_schema or "tristan.any"
            output_schema = spec.output_schema or "tristan.any"
            if not self.schemas.compatible(current, input_schema):
                raise ValueError(
                    f"Schema mismatch before {capability_id!r}: {current!r} is not compatible with {input_schema!r}"
                )
            steps.append(CompiledStep(spec.id, provider.plugin, input_schema, output_schema))
            current = output_schema
        return PipelinePlan(tuple(steps), initial_schema, current)

    def find_path(self, *, source_schema: str, target_schema: str, max_steps: int = 6) -> PipelinePlan:
        if self.schemas.compatible(source_schema, target_schema):
            return PipelinePlan((), source_schema, source_schema)
        providers: list[CapabilityProvider] = [
            provider
            for capability_id in self.capabilities.capability_ids()
            for provider in self.capabilities.providers(capability_id)
        ]
        queue = deque([(source_schema, tuple())])
        visited: set[tuple[str, int]] = {(source_schema, 0)}
        while queue:
            current_schema, path = queue.popleft()
            if len(path) >= max_steps:
                continue
            for provider in providers:
                spec = provider.capability
                input_schema = spec.input_schema or "tristan.any"
                output_schema = spec.output_schema or "tristan.any"
                if not self.schemas.compatible(current_schema, input_schema):
                    continue
                step = CompiledStep(spec.id, provider.plugin, input_schema, output_schema)
                next_path = path + (step,)
                if self.schemas.compatible(output_schema, target_schema):
                    return PipelinePlan(next_path, source_schema, output_schema)
                state = (output_schema, len(next_path))
                if state not in visited:
                    visited.add(state)
                    queue.append((output_schema, next_path))
        raise KeyError(f"No schema-compatible pipeline from {source_schema!r} to {target_schema!r} within {max_steps} steps")
