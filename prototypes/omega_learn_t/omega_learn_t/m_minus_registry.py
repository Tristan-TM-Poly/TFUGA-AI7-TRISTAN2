from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Iterable, List

from .core import ErrorRecord


class MMinusRegistry:
    """Registry turning mistakes into anti-fragile learning assets."""

    def __init__(self, errors: Iterable[ErrorRecord] = ()) -> None:
        self.errors: List[ErrorRecord] = list(errors)

    def add(self, error: ErrorRecord) -> None:
        self.errors.append(error)

    def to_dicts(self) -> List[dict]:
        return [asdict(error) for error in self.errors]

    def top_causes(self, limit: int = 5) -> List[tuple[str, int]]:
        return Counter(error.cause for error in self.errors).most_common(limit)

    def future_tests(self) -> List[str]:
        return [error.future_test for error in self.errors if error.future_test]

    def oak_residue(self) -> float:
        if not self.errors:
            return 0.0
        open_errors = [e for e in self.errors if e.status_oak != "resolved"]
        return min(1.0, sum(e.severity for e in open_errors) / (len(self.errors) * 3.0))
