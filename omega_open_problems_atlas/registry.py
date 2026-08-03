"""Deterministic in-memory and JSONL registry."""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from typing import Iterable

from .models import ProblemGenome
from .oak import evaluate_problem


class DuplicateProblemError(ValueError):
    pass


class ProblemRegistry:
    def __init__(self, problems: Iterable[ProblemGenome] = ()) -> None:
        self._problems: dict[str, ProblemGenome] = {}
        self._statement_hashes: dict[str, str] = {}
        for problem in problems:
            self.add(problem)

    def add(self, problem: ProblemGenome) -> None:
        if problem.problem_id in self._problems:
            raise DuplicateProblemError(f"duplicate problem_id: {problem.problem_id}")
        digest = problem.statement_hash()
        if digest in self._statement_hashes:
            other = self._statement_hashes[digest]
            raise DuplicateProblemError(
                f"duplicate normalized statement: {problem.problem_id} == {other}"
            )
        self._problems[problem.problem_id] = problem
        self._statement_hashes[digest] = problem.problem_id

    def get(self, problem_id: str) -> ProblemGenome:
        return self._problems[problem_id]

    def values(self) -> tuple[ProblemGenome, ...]:
        return tuple(self._problems[key] for key in sorted(self._problems))

    def update(self, problem_id: str, **changes: object) -> ProblemGenome:
        old = self.get(problem_id)
        candidate = replace(old, **changes)
        old_hash = old.statement_hash()
        new_hash = candidate.statement_hash()
        if new_hash != old_hash and new_hash in self._statement_hashes:
            raise DuplicateProblemError("updated statement duplicates another record")
        self._problems[problem_id] = candidate
        self._statement_hashes.pop(old_hash, None)
        self._statement_hashes[new_hash] = problem_id
        return candidate

    def summary(self) -> dict[str, object]:
        open_counts = Counter(p.open_status.value for p in self.values())
        domain_counts = Counter(d for p in self.values() for d in p.domains)
        decisions = Counter(evaluate_problem(p).decision.value for p in self.values())
        return {
            "problem_count": len(self._problems),
            "open_status_counts": dict(sorted(open_counts.items())),
            "domain_counts": dict(sorted(domain_counts.items())),
            "oak_decisions": dict(sorted(decisions.items())),
            "solution_claimed_count": sum(p.solution_claimed for p in self.values()),
            "all_finite_computation_boundaries_present": all(
                p.finite_computation_is_not_proof for p in self.values()
            ),
        }

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(p.normalized_payload(), sort_keys=True, ensure_ascii=False)
            for p in self.values()
        ]
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
