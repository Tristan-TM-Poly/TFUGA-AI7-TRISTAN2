from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from .hashing import stable_id
from .models import FrontierCell, ProvenanceRecord, TaskIR
from .task_ir import TaskIRCompiler


class TaskGenerator(Protocol):
    generator_id: str

    def generate(
        self,
        cell: FrontierCell,
        provenance: ProvenanceRecord,
        ordinal: int,
    ) -> TaskIR: ...


@dataclass(frozen=True)
class ParametricTaskGenerator:
    compiler: TaskIRCompiler = TaskIRCompiler()
    generator_id: str = "omega.parametric.v1"

    def generate(
        self,
        cell: FrontierCell,
        provenance: ProvenanceRecord,
        ordinal: int,
    ) -> TaskIR:
        return self.compiler.compile(cell, provenance, ordinal)


@dataclass(frozen=True)
class GeneratorRegistry:
    generators: tuple[TaskGenerator, ...]

    def __post_init__(self) -> None:
        ids = [generator.generator_id for generator in self.generators]
        if len(set(ids)) != len(ids):
            raise ValueError("generator identifiers must be unique")
        if not self.generators:
            raise ValueError("at least one generator must be registered")

    def select(self, cell: FrontierCell) -> TaskGenerator:
        index_seed = stable_id("generator", cell.to_dict(), length=8)
        index = int(index_seed.rsplit("-", 1)[1], 16) % len(self.generators)
        return self.generators[index]

    def generate_many(
        self,
        cells: Iterable[tuple[int, FrontierCell]],
        provenance: ProvenanceRecord,
    ) -> tuple[TaskIR, ...]:
        tasks: list[TaskIR] = []
        for ordinal, cell in cells:
            generator = self.select(cell)
            tasks.append(generator.generate(cell, provenance, ordinal))
        return tuple(tasks)


DEFAULT_GENERATORS = GeneratorRegistry((ParametricTaskGenerator(),))
