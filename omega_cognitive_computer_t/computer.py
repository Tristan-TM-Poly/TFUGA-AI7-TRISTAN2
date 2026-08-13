from __future__ import annotations

from dataclasses import dataclass

from .cir import CognitiveState
from .compiler import CognitiveCompiler
from .isa import Program
from .memory import CognitiveMemory
from .runtime import CognitiveRuntime, ExecutionResult, RuntimeContext


@dataclass
class CognitiveComputer:
    compiler: CognitiveCompiler
    runtime: CognitiveRuntime
    memory: CognitiveMemory

    @classmethod
    def default(cls) -> "CognitiveComputer":
        return cls(CognitiveCompiler(), CognitiveRuntime(), CognitiveMemory())

    def compile(self, problem: str) -> Program:
        return self.compiler.compile(problem)

    def execute(self, problem: str, state: CognitiveState | None = None, *, context: RuntimeContext | None = None) -> ExecutionResult:
        initial = state or CognitiveState(goals=[problem], provenance=["user_intent"])
        program = self.compile(problem)
        ctx = context or RuntimeContext()
        ctx.problem_text = problem
        ctx.memory = ctx.memory or self.memory
        return self.runtime.run(program, initial, context=ctx)
