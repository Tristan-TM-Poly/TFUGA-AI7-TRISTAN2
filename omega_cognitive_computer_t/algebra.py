from __future__ import annotations

from dataclasses import dataclass
import json

from .cir import CognitiveState
from .isa import Instruction, OperatorRegistry, Program, default_registry
from .runtime import CognitiveRuntime, RuntimeContext


def compose(name: str, *programs: Program) -> Program:
    instructions = tuple(inst for p in programs for inst in p.instructions)
    tags = tuple(dict.fromkeys(tag for p in programs for tag in p.tags))
    return Program(name=name, instructions=instructions, tags=tags)


def dual_program(program: Program, registry: OperatorRegistry | None = None) -> Program:
    reg = registry or default_registry()
    out: list[Instruction] = []
    for inst in reversed(program.instructions):
        dual = reg.dual(inst.opcode)
        if dual is None:
            raise ValueError(f"No declared dual for {inst.opcode.value}")
        out.append(Instruction(dual, inst.args, dict(inst.options)))
    return Program(name=f"dual({program.name})", instructions=tuple(out), tags=program.tags)


def _top_level_distance(a: CognitiveState, b: CognitiveState) -> float:
    da, db = a.to_dict(), b.to_dict()
    keys = sorted(set(da) | set(db))
    if not keys:
        return 0.0
    changed = sum(json.dumps(da.get(k), sort_keys=True) != json.dumps(db.get(k), sort_keys=True) for k in keys)
    return changed / len(keys)


@dataclass(frozen=True)
class CommutatorReport:
    distance: float
    ab_fingerprint: str
    ba_fingerprint: str


def commutator(a: Instruction, b: Instruction, state: CognitiveState, *, runtime: CognitiveRuntime | None = None) -> CommutatorReport:
    rt = runtime or CognitiveRuntime()
    ab = rt.run(Program("AB", (a, b)), state, context=RuntimeContext(budget=100)).state
    ba = rt.run(Program("BA", (b, a)), state, context=RuntimeContext(budget=100)).state
    return CommutatorReport(_top_level_distance(ab, ba), ab.fingerprint(), ba.fingerprint())


def idempotence_distance(inst: Instruction, state: CognitiveState, *, runtime: CognitiveRuntime | None = None) -> float:
    rt = runtime or CognitiveRuntime()
    once = rt.run(Program("once", (inst,)), state, context=RuntimeContext(budget=100)).state
    twice = rt.run(Program("twice", (inst, inst)), state, context=RuntimeContext(budget=100)).state
    return _top_level_distance(once, twice)
