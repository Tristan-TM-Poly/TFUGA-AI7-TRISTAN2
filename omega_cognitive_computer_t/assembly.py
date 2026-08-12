from __future__ import annotations

import shlex

from .isa import ALIASES, Instruction, Opcode, Program


class AssemblyError(ValueError):
    pass


def resolve_opcode(token: str) -> Opcode:
    name = token.strip().upper()
    if name in ALIASES:
        return ALIASES[name]
    try:
        return Opcode[name]
    except KeyError:
        try:
            return Opcode(name)
        except ValueError as exc:
            raise AssemblyError(f"Unknown cognitive opcode: {token}") from exc


def parse_assembly(text: str, *, name: str = "assembly") -> Program:
    instructions: list[Instruction] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError as exc:
            raise AssemblyError(f"Line {line_no}: {exc}") from exc
        if not parts:
            continue
        opcode = resolve_opcode(parts[0])
        instructions.append(Instruction(opcode, tuple(parts[1:])))
    if not instructions:
        raise AssemblyError("Cognitive assembly program is empty")
    return Program(name=name, instructions=tuple(instructions), tags=("assembly",))


def render_assembly(program: Program) -> str:
    return "\n".join(str(i) for i in program.instructions) + "\n"
