from __future__ import annotations

import math

from .ir import validate_program
from .models import AnalysisMetrics, Program


def dependency_graph(program: Program) -> dict[int, tuple[int, ...]]:
    validate_program(program)
    producer: dict[str, int] = {}
    graph: dict[int, tuple[int, ...]] = {}
    for index, instruction in enumerate(program.instructions):
        deps = sorted(
            {
                producer[value]
                for value in instruction.inputs
                if not value.startswith("#") and value in producer
            }
        )
        graph[index] = tuple(deps)
        if instruction.output is not None:
            producer[instruction.output] = index
    return graph


def critical_path(program: Program) -> float:
    graph = dependency_graph(program)
    finish: dict[int, float] = {}
    for index, instruction in enumerate(program.instructions):
        start = max((finish[parent] for parent in graph[index]), default=0.0)
        finish[index] = start + instruction.latency
    if not finish:
        return 0.0
    output_producers = {
        instruction.output: index
        for index, instruction in enumerate(program.instructions)
        if instruction.output is not None
    }
    terminal = [output_producers[name] for name in program.outputs if name in output_producers]
    return max((finish[index] for index in terminal), default=max(finish.values()))


def _last_uses(program: Program) -> dict[str, int]:
    last: dict[str, int] = {}
    for index, instruction in enumerate(program.instructions):
        for value in instruction.inputs:
            if not value.startswith("#"):
                last[value] = index
    terminal = len(program.instructions)
    for value in program.outputs:
        last[value] = terminal
    return last


def register_lifetime_metrics(program: Program) -> tuple[int, int]:
    """Return proxy register-time volume and peak live values.

    Program inputs are considered live before instruction 0 (birth = -1). This
    avoids the old undercount where argument values contributed no pressure.
    The metric remains an SSA liveness proxy, not a physical register allocator.
    """

    validate_program(program)
    last = _last_uses(program)
    birth: dict[str, int] = {value: -1 for value in program.inputs}
    birth.update(
        {
            instruction.output: index
            for index, instruction in enumerate(program.instructions)
            if instruction.output is not None
        }
    )
    volume = sum(max(0, last.get(value, born) - born) for value, born in birth.items())
    peak = 0
    for time in range(-1, len(program.instructions) + 1):
        live = sum(
            1
            for value, born in birth.items()
            if born <= time <= last.get(value, born)
        )
        peak = max(peak, live)
    return volume, peak


def binary_entropy(probability: float) -> float:
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be finite and inside [0, 1]")
    if probability in {0.0, 1.0}:
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def analyze(program: Program) -> AnalysisMetrics:
    validate_program(program)
    count = len(program.instructions)
    path = critical_path(program)
    volume, peak = register_lifetime_metrics(program)
    memory_bytes = sum(instruction.memory_bytes for instruction in program.instructions)
    branch_entropy = sum(
        binary_entropy(instruction.branch_probability)
        for instruction in program.instructions
        if instruction.branch_probability is not None
    )
    mean_vector_width = (
        sum(instruction.vector_width for instruction in program.instructions) / count
        if count
        else 0.0
    )
    useful_ops = sum(
        1
        for instruction in program.instructions
        if instruction.op not in {"load", "store", "branch", "const", "move"}
    )
    intensity = useful_ops / memory_bytes if memory_bytes else None
    return AnalysisMetrics(
        instruction_count=count,
        critical_path=path,
        ilp_upper_bound=(count / path if path > 0 else float(count > 0)),
        register_time_volume=volume,
        peak_live_values=peak,
        memory_bytes=memory_bytes,
        branch_entropy_bits=branch_entropy,
        mean_vector_width=mean_vector_width,
        useful_ops_per_memory_byte=intensity,
    )


def cvcd_signature(program: Program) -> dict[str, float | int | None]:
    """Compact ASM-CVCD signature for comparison, not a universal performance model."""

    metrics = analyze(program)
    return {
        "F_instruction_count": metrics.instruction_count,
        "D_critical_path": metrics.critical_path,
        "M_memory_bytes": metrics.memory_bytes,
        "R_register_time_volume": metrics.register_time_volume,
        "R_peak_live_values": metrics.peak_live_values,
        "B_branch_entropy_bits": metrics.branch_entropy_bits,
        "V_mean_vector_width": metrics.mean_vector_width,
        "C_ilp_upper_bound": metrics.ilp_upper_bound,
        "I_useful_ops_per_memory_byte": metrics.useful_ops_per_memory_byte,
    }
