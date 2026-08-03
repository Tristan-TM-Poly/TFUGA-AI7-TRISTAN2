from __future__ import annotations

from math import ceil, log2
from typing import Mapping, Sequence

from .models import BisectPlan, BisectStep


class BisectPlanner:
    """Pure planner: computes the next discriminating commit but never runs Git."""

    def plan(
        self,
        failure_id: str,
        ordered_commits: Sequence[str],
        known_good_sha: str,
        known_bad_sha: str,
        *,
        tested_verdicts: Mapping[str, str] | None = None,
    ) -> BisectPlan:
        commits = tuple(str(value) for value in ordered_commits)
        if len(commits) < 2 or len(commits) != len(set(commits)):
            raise ValueError("ordered_commits must contain at least two unique commits")
        if known_good_sha not in commits or known_bad_sha not in commits:
            raise KeyError("known good and bad commits must be in ordered_commits")
        good_index = commits.index(known_good_sha)
        bad_index = commits.index(known_bad_sha)
        if good_index >= bad_index:
            raise ValueError("known_good_sha must precede known_bad_sha")
        verdicts = {str(key): str(value).upper() for key, value in (tested_verdicts or {}).items()}
        for sha, verdict in verdicts.items():
            if sha not in commits:
                raise KeyError(f"tested verdict references unknown commit: {sha}")
            if verdict not in {"GOOD", "BAD"}:
                raise ValueError("verdicts must be GOOD or BAD")

        lower = good_index
        upper = bad_index
        for sha, verdict in verdicts.items():
            index = commits.index(sha)
            if verdict == "GOOD" and lower < index < upper:
                lower = index
            elif verdict == "BAD" and lower < index < upper:
                upper = index
        remaining = upper - lower - 1
        if remaining <= 0:
            status = "BOUNDARY_IDENTIFIED"
            next_step = None
            maximum = 0
        else:
            candidate_index = lower + ((upper - lower) // 2)
            if candidate_index == lower:
                candidate_index += 1
            next_step = BisectStep(
                candidate_sha=commits[candidate_index],
                lower_good_sha=commits[lower],
                upper_bad_sha=commits[upper],
                remaining_candidates=remaining,
            )
            maximum = int(ceil(log2(remaining + 1)))
            status = "NEXT_EVALUATION_PLANNED"
        return BisectPlan(
            failure_id=failure_id,
            ordered_commits=commits,
            known_good_sha=commits[lower],
            known_bad_sha=commits[upper],
            next_step=next_step,
            maximum_remaining_evaluations=maximum,
            tested_verdicts=verdicts,
            status=status,
        )
