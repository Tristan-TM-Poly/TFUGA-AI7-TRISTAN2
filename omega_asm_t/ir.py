from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .models import Instruction, Program


def _instruction_from_dict(data: dict[str, Any]) -> Instruction:
    return Instruction(
        op=str(data["op"]),
        output=data.get("output"),
        inputs=tuple(str(value) for value in data.get("inputs", ())),
        latency=float(data.get("latency", 1.0)),
        size_bytes=int(data.get("size_bytes", 4)),
        memory_bytes=int(data.get("memory_bytes", 0)),
        branch_probability=(
            None
            if data.get("branch_probability") is None
            else float(data["branch_probability"])
        ),
        vector_width=int(data.get("vector_width", 1)),
        metadata=dict(data.get("metadata", {})),
    )


def program_from_dict(data: dict[str, Any]) -> Program:
    program = Program(
        name=str(data.get("name", "anonymous")),
        inputs=tuple(str(value) for value in data.get("inputs", ())),
        instructions=tuple(
            _instruction_from_dict(item) for item in data.get("instructions", ())
        ),
        outputs=tuple(str(value) for value in data.get("outputs", ())),
    )
    validate_program(program)
    return program


def load_program(path: str | Path) -> Program:
    return program_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def dump_program(program: Program, path: str | Path) -> None:
    validate_program(program)
    Path(path).write_text(
        json.dumps(program.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_identifier(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}: identifier must be a non-empty string")
    if value.startswith("#"):
        raise ValueError(f"{context}: '#' prefix is reserved for immediate values")
    return value


def validate_program(program: Program) -> None:
    if not isinstance(program.name, str) or not program.name.strip():
        raise ValueError("program name must be a non-empty string")

    inputs = tuple(
        _validate_identifier(value, context="program input") for value in program.inputs
    )
    if len(set(inputs)) != len(inputs):
        raise ValueError("program inputs must be unique")

    available = set(inputs)
    produced: set[str] = set()
    for index, instruction in enumerate(program.instructions):
        if not isinstance(instruction.op, str) or not instruction.op.strip():
            raise ValueError(f"instruction {index}: op must be a non-empty string")
        if not math.isfinite(instruction.latency) or instruction.latency < 0:
            raise ValueError(f"instruction {index}: latency must be finite and non-negative")
        if (
            not isinstance(instruction.size_bytes, int)
            or isinstance(instruction.size_bytes, bool)
            or instruction.size_bytes < 0
            or not isinstance(instruction.memory_bytes, int)
            or isinstance(instruction.memory_bytes, bool)
            or instruction.memory_bytes < 0
        ):
            raise ValueError(f"instruction {index}: byte counts must be non-negative integers")
        if (
            not isinstance(instruction.vector_width, int)
            or isinstance(instruction.vector_width, bool)
            or instruction.vector_width < 1
        ):
            raise ValueError(f"instruction {index}: vector width must be a positive integer")
        if instruction.branch_probability is not None and (
            not math.isfinite(instruction.branch_probability)
            or not 0.0 <= instruction.branch_probability <= 1.0
        ):
            raise ValueError(f"instruction {index}: branch probability outside [0, 1]")
        if not isinstance(instruction.metadata, dict):
            raise ValueError(f"instruction {index}: metadata must be a dictionary")

        missing: list[str] = []
        for value in instruction.inputs:
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"instruction {index}: inputs must be non-empty strings"
                )
            if value == "#":
                raise ValueError(f"instruction {index}: empty immediate value")
            if not value.startswith("#") and value not in available:
                missing.append(value)
        if missing:
            raise ValueError(f"instruction {index}: undefined inputs {missing}")

        if instruction.output is not None:
            output = _validate_identifier(
                instruction.output, context=f"instruction {index} output"
            )
            if output in produced or output in available:
                raise ValueError(
                    f"instruction {index}: output {output!r} is not SSA-unique"
                )
            produced.add(output)
            available.add(output)

    unknown_outputs: list[str] = []
    for value in program.outputs:
        output = _validate_identifier(value, context="program output")
        if output not in available:
            unknown_outputs.append(output)
    if unknown_outputs:
        raise ValueError(f"undefined program outputs: {unknown_outputs}")


def dot_u64_block_program(width: int = 4) -> Program:
    """Return an unrolled SSA block used for static optimization experiments.

    This is deliberately a block, not a complete loop. Native loop correctness is
    tested separately by the built-in x86-64 assembly fixture. Load offsets are
    carried as metadata because address lowering is a backend concern in ASM-IR.
    """

    if width <= 0:
        raise ValueError("width must be positive")
    instructions: list[Instruction] = []
    products: list[str] = []
    for index in range(width):
        a = f"a{index}"
        b = f"b{index}"
        product = f"p{index}"
        offset = index * 8
        instructions.extend(
            [
                Instruction(
                    "load",
                    a,
                    ("a_ptr",),
                    latency=4.0,
                    memory_bytes=8,
                    metadata={"offset_bytes": offset},
                ),
                Instruction(
                    "load",
                    b,
                    ("b_ptr",),
                    latency=4.0,
                    memory_bytes=8,
                    metadata={"offset_bytes": offset},
                ),
                Instruction("mul", product, (a, b), latency=3.0),
            ]
        )
        products.append(product)

    layer = products
    round_index = 0
    while len(layer) > 1:
        next_layer: list[str] = []
        for index in range(0, len(layer), 2):
            if index + 1 == len(layer):
                next_layer.append(layer[index])
                continue
            output = f"sum_{round_index}_{index // 2}"
            instructions.append(
                Instruction("add", output, (layer[index], layer[index + 1]), latency=1.0)
            )
            next_layer.append(output)
        layer = next_layer
        round_index += 1
    result = layer[0]
    program = Program(
        name=f"dot_u64_block_{width}",
        inputs=("a_ptr", "b_ptr"),
        instructions=tuple(instructions),
        outputs=(result,),
    )
    validate_program(program)
    return program
