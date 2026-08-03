from __future__ import annotations

from math import ceil
from typing import Callable, Sequence

from .models import ReproductionReceipt


class DeltaMinimizer:
    """Deterministic ddmin-style reducer for finite local fixtures."""

    def minimize(
        self,
        failure_id: str,
        items: Sequence[str],
        predicate: Callable[[tuple[str, ...]], bool],
        *,
        max_evaluations: int = 256,
    ) -> ReproductionReceipt:
        original = tuple(str(item) for item in items)
        if not original:
            raise ValueError("items cannot be empty")
        if max_evaluations < 1:
            raise ValueError("max_evaluations must be positive")
        evaluations = 1
        if not predicate(original):
            raise ValueError("original fixture does not reproduce the failure")
        current = original
        granularity = 2
        trace: list[dict[str, object]] = []
        limit_reached = False

        while len(current) >= 2:
            chunk_size = int(ceil(len(current) / granularity))
            reduced = False
            for start in range(0, len(current), chunk_size):
                if evaluations >= max_evaluations:
                    limit_reached = True
                    break
                complement = current[:start] + current[start + chunk_size:]
                if not complement:
                    continue
                evaluations += 1
                preserves = predicate(complement)
                trace.append({
                    "granularity": granularity,
                    "removed_start": start,
                    "removed_count": min(chunk_size, len(current) - start),
                    "candidate_size": len(complement),
                    "preserved_failure": preserves,
                })
                if preserves:
                    current = complement
                    granularity = max(2, granularity - 1)
                    reduced = True
                    break
            if limit_reached:
                break
            if not reduced:
                if granularity >= len(current):
                    break
                granularity = min(len(current), granularity * 2)

        preserved = predicate(current)
        evaluations += 1
        return ReproductionReceipt(
            failure_id=failure_id,
            original_items=original,
            minimized_items=current,
            evaluations=evaluations,
            preserved_failure=preserved,
            limit_reached=limit_reached,
            reduction_ratio=1.0 - (len(current) / len(original)),
            trace=tuple(trace),
        )

    def minimize_required_tokens_fixture(
        self,
        failure_id: str,
        items: Sequence[str],
        required_tokens: Sequence[str],
        *,
        max_evaluations: int = 256,
    ) -> ReproductionReceipt:
        required = set(str(item) for item in required_tokens)
        if not required:
            raise ValueError("required_tokens cannot be empty")
        return self.minimize(
            failure_id,
            items,
            lambda candidate: required.issubset(set(candidate)),
            max_evaluations=max_evaluations,
        )
