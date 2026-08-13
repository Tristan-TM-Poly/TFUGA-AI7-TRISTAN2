from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import factorial
from typing import Callable, Iterable

from .isa import Instruction, Program


ScoreFn = Callable[[Program], float]


def ablation_profile(program: Program, score: ScoreFn) -> dict[int, float]:
    baseline = score(program)
    return {i: baseline - score(program.without_indices({i})) for i in range(len(program.instructions))}


def shapley_by_instruction(program: Program, score: ScoreFn, *, max_instructions: int = 9) -> dict[int, float]:
    n = len(program.instructions)
    if n > max_instructions:
        raise ValueError(f"Exact Shapley is exponential; n={n} exceeds max_instructions={max_instructions}")
    players = tuple(range(n))
    result = {i: 0.0 for i in players}
    denom = factorial(n)
    for i in players:
        others = [j for j in players if j != i]
        for r in range(len(others) + 1):
            for subset_tuple in combinations(others, r):
                subset = set(subset_tuple)
                weight = factorial(len(subset)) * factorial(n - len(subset) - 1) / denom
                keep_s = tuple(inst for idx, inst in enumerate(program.instructions) if idx in subset)
                keep_si = tuple(inst for idx, inst in enumerate(program.instructions) if idx in subset | {i})
                result[i] += weight * (score(Program("coalition+i", keep_si)) - score(Program("coalition", keep_s)))
    return result


def pairwise_synergy(program: Program, score: ScoreFn) -> dict[tuple[int, int], float]:
    empty = score(Program("empty", ()))
    result: dict[tuple[int, int], float] = {}
    for i, j in combinations(range(len(program.instructions)), 2):
        pi = Program("i", (program.instructions[i],))
        pj = Program("j", (program.instructions[j],))
        pij = Program("ij", (program.instructions[i], program.instructions[j]))
        result[(i, j)] = score(pij) - score(pi) - score(pj) + empty
    return result


def discover_meta_skills(traces: Iterable[Iterable[Instruction]], *, n: int = 3, min_count: int = 2) -> list[tuple[int, tuple[str, ...]]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for trace in traces:
        seq = [inst.opcode.value for inst in trace]
        counts.update(tuple(seq[i:i+n]) for i in range(max(0, len(seq) - n + 1)))
    return sorted(((count, gram) for gram, count in counts.items() if count >= min_count), reverse=True)
