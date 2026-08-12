from __future__ import annotations

from .isa import Instruction, Opcode, Program


def _p(name: str, *items: Instruction) -> Program:
    return Program(name=name, instructions=tuple(items), tags=("tristan", "superinstruction"))


TRISTAN_EXPLORE = _p(
    "TRISTAN_EXPLORE",
    Instruction(Opcode.REPRESENT, ("algebraic",)),
    Instruction(Opcode.REPRESENT, ("geometric",)),
    Instruction(Opcode.ZOOM),
    Instruction(Opcode.DEZOOM),
    Instruction(Opcode.EXPAND),
    Instruction(Opcode.TRANSFER),
)

TRISTAN_COMPRESS = _p(
    "TRISTAN_COMPRESS",
    Instruction(Opcode.MERGE),
    Instruction(Opcode.INVARIANTS),
    Instruction(Opcode.COMPRESS),
)

TRISTAN_ATTACK = _p(
    "TRISTAN_ATTACK",
    Instruction(Opcode.COUNTER),
    Instruction(Opcode.ATTACK),
    Instruction(Opcode.CONTRADICT),
    Instruction(Opcode.RESIDUAL),
)

TRISTAN_CRYSTALLIZE = _p(
    "TRISTAN_CRYSTALLIZE",
    Instruction(Opcode.CONCRETIZE),
    Instruction(Opcode.BENCHMARK),
    Instruction(Opcode.OAK),
    Instruction(Opcode.CRYSTALLIZE),
)

TRISTAN_DISCOVER = Program(
    name="TRISTAN_DISCOVER",
    instructions=TRISTAN_EXPLORE.instructions + TRISTAN_COMPRESS.instructions + TRISTAN_ATTACK.instructions + TRISTAN_CRYSTALLIZE.instructions,
    tags=("tristan", "discovery", "superinstruction"),
)

SUPERINSTRUCTIONS = {p.name: p for p in (TRISTAN_EXPLORE, TRISTAN_COMPRESS, TRISTAN_ATTACK, TRISTAN_CRYSTALLIZE, TRISTAN_DISCOVER)}
