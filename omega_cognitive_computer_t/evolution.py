from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Callable

from .isa import Instruction, OperatorRegistry, Program, default_registry


@dataclass(frozen=True)
class EvolutionCandidate:
    program: Program
    fitness: float


class CognitiveEvolution:
    """Small, explicit program-evolution scaffold. Fitness must come from an external benchmark."""

    def __init__(self, registry: OperatorRegistry | None = None, *, seed: int = 0) -> None:
        self.registry = registry or default_registry()
        self.random = random.Random(seed)

    def mutate(self, program: Program) -> Program:
        items = list(program.instructions)
        if not items:
            return program
        idx = self.random.randrange(len(items))
        dual = self.registry.dual(items[idx].opcode)
        if dual is not None:
            items[idx] = Instruction(dual, items[idx].args, dict(items[idx].options))
        elif len(items) > 1:
            items.pop(idx)
        return Program(f"{program.name}:mut", tuple(items), program.tags, {**program.metadata, "mutation": "dual_or_drop"})

    def crossover(self, a: Program, b: Program) -> Program:
        cut_a = len(a.instructions) // 2
        cut_b = len(b.instructions) // 2
        return Program(f"cross({a.name},{b.name})", a.instructions[:cut_a] + b.instructions[cut_b:], tuple(dict.fromkeys((*a.tags, *b.tags))))

    def select(self, programs: list[Program], fitness: Callable[[Program], float], *, keep: int = 3) -> list[EvolutionCandidate]:
        ranked = [EvolutionCandidate(p, fitness(p)) for p in programs]
        ranked.sort(key=lambda x: x.fitness, reverse=True)
        return ranked[:keep]
