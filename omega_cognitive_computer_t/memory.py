from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Iterable

from .cir import CognitiveState
from .isa import Program

_TOKEN = re.compile(r"[A-Za-zÀ-ÿ0-9_]+")


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN.finditer(text)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class MemoryRecord:
    state_fingerprint: str
    problem_text: str
    strategy: tuple[str, ...]
    outcome: str
    score: float
    failure_modes: tuple[str, ...] = ()
    notes: str = ""


class CognitiveMemory:
    """In-memory M+/M- strategy cache. Persistence is explicit, never implicit."""

    def __init__(self) -> None:
        self.positive: list[MemoryRecord] = []
        self.negative: list[MemoryRecord] = []

    def remember_positive(self, state: CognitiveState, problem_text: str, program: Program, *, score: float, notes: str = "") -> MemoryRecord:
        rec = MemoryRecord(state.fingerprint(), problem_text, tuple(op.value for op in program.opcodes()), "success", score, notes=notes)
        self.positive.append(rec)
        return rec

    def remember_negative(self, state: CognitiveState, problem_text: str, program: Program, *, score: float, failure_modes: Iterable[str], notes: str = "") -> MemoryRecord:
        rec = MemoryRecord(state.fingerprint(), problem_text, tuple(op.value for op in program.opcodes()), "failure", score, tuple(failure_modes), notes)
        self.negative.append(rec)
        return rec

    def nearest(self, problem_text: str, *, include_negative: bool = False, limit: int = 5) -> list[tuple[float, MemoryRecord]]:
        corpus = list(self.positive) + (list(self.negative) if include_negative else [])
        q = _tokens(problem_text)
        scored = [(_jaccard(q, _tokens(r.problem_text)), r) for r in corpus]
        scored.sort(key=lambda x: (x[0], x[1].score), reverse=True)
        return scored[:limit]

    def exact(self, state: CognitiveState) -> tuple[MemoryRecord, ...]:
        fp = state.fingerprint()
        return tuple(r for r in (*self.positive, *self.negative) if r.state_fingerprint == fp)

    def to_json(self) -> str:
        return json.dumps({"positive": [asdict(r) for r in self.positive], "negative": [asdict(r) for r in self.negative]}, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "CognitiveMemory":
        payload = json.loads(text)
        mem = cls()
        mem.positive = [MemoryRecord(**{**x, "strategy": tuple(x["strategy"]), "failure_modes": tuple(x.get("failure_modes", ()))}) for x in payload.get("positive", [])]
        mem.negative = [MemoryRecord(**{**x, "strategy": tuple(x["strategy"]), "failure_modes": tuple(x.get("failure_modes", ()))}) for x in payload.get("negative", [])]
        return mem
