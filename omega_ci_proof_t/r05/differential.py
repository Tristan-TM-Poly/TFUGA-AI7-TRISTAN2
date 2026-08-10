from __future__ import annotations

from typing import Sequence

from .behaviors import resolve_behavior
from .models import DifferentialDivergence, DifferentialReport


class DifferentialOracle:
    def compare(
        self,
        *,
        reference_behavior: str,
        candidate_behaviors: Sequence[str],
        corpus: Sequence[str],
        claim_id: str,
    ) -> DifferentialReport:
        reference = resolve_behavior(reference_behavior)
        divergences: list[DifferentialDivergence] = []
        agreements = 0
        for behavior_name in sorted(set(candidate_behaviors)):
            candidate = resolve_behavior(behavior_name)
            for value in corpus:
                expected = reference(value)
                observed = candidate(value)
                if expected == observed:
                    agreements += 1
                else:
                    divergences.append(DifferentialDivergence(
                        behavior=behavior_name,
                        input_value=value,
                        reference_output=expected,
                        candidate_output=observed,
                        claim_id=claim_id,
                    ))
        return DifferentialReport(
            reference_behavior=reference_behavior,
            candidate_behaviors=tuple(sorted(set(candidate_behaviors))),
            corpus_size=len(tuple(corpus)),
            divergences=tuple(divergences),
            agreements=agreements,
        )
