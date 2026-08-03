from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable

from .models import SubmissionReport


@dataclass
class MMinusLedger:
    counts: Counter[str] = field(default_factory=Counter)
    examples: dict[str, dict[str, str]] = field(default_factory=dict)

    def absorb(self, report: SubmissionReport) -> None:
        for failure in report.failures:
            self.counts[failure.fingerprint] += 1
            self.examples.setdefault(
                failure.fingerprint,
                {
                    "task_id": failure.task_id,
                    "case_name": failure.case_name,
                    "kind": failure.kind,
                    "input": failure.input_repr,
                    "expected": failure.expected_repr,
                    "observed": failure.observed_repr,
                },
            )

    def absorb_many(self, reports: Iterable[SubmissionReport]) -> None:
        for report in reports:
            self.absorb(report)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unique_failure_signatures": len(self.counts),
            "total_failures": sum(self.counts.values()),
            "records": [
                {
                    "fingerprint": fingerprint,
                    "count": self.counts[fingerprint],
                    **self.examples[fingerprint],
                }
                for fingerprint in sorted(self.counts)
            ],
        }
