from __future__ import annotations

import json
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
        vector_width=max(1, int(data.get("vector_width", 1))),
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
    Path(path).write_text(
        json.dumps(program.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_program(program: Program) -> None:
    available = set(program.inputs)
    produced: set[str] = set()
    for index, instruction in enumerate(program.instructions):
        if instruction.latency < 0:
            raise ValueError(f"instruction {index}: latency must be non-negative")
        if instruction.size_bytes < 0 or instruction.memory_bytes < 0:
            raise ValueError(f"instruction {index}: byte counts must be non-negative")
        if instruction.branch_probability is not None and not (
            0.0 <= instruction.branch_probability <= 1.0
        ):
            raise ValueError(f"instruction {index}: branch probability outside [0, 1]")
        missing = [
            value
            for value in instruction.inputs
            if not value.startswith("#") and value not in available
        ]
        if missing:
            raise ValueError(f"instruction {index}: undefined inputs {missing}")
        if instruction.output is not None:
            if instruction.output in produced or instruction.output in program.inputs:
                raise ValueError(
                    f"instruction {index}: output {instruction.output!r} is not SSA-unique"
                )
            produced.add(instruction.output)
            available.add(instruction.output)
    unknown_outputs = [value for value in program.outputs if value not in available]
    if unknown_outputs:
        raise ValueError(f"undefined program outputs: {unknown_outputs}")


def dot_u64_block_program(width: int = 4) -> Program:
    """Return an unrolled SSA block used for static optimization experiments.

    This is deliberately a block, not a complete loop. Native loop correctness is
    tested separately by the built-in x86-64 assembly fixture.
    """

    if width <= 0:
        raise ValueError("width must be positive")
    instructions: list[Instruction] = [
        Instruction("const", "zero", ("#0",), latency=0.0, size_bytes=2)
    ]
    products: list[str] = []
    for index in range(width):
        a = f"a{index}"
        b = f"b{index}"
        product = f"p{index}"
        instructions.extend(
            [
                Instruction("load", a, ("a_ptr",), latency=4.0, memory_bytes=8),
                Instruction("load", b, ("b_ptr",), latency=4.0, memory_bytes=8),
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
    return Program(
        name=f"dot_u64_block_{width}",
        inputs=("a_ptr", "b_ptr"),
        instructions=tuple(instructions),
        outputs=(result,),
    )
