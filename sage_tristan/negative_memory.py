"""Negative memory for Omega Math Tristan.

Negative memory turns failed reasoning patterns into anti-patterns and
replacement rules. It is a research immune system for proof hygiene,
baseline discipline and claim calibration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

FailureType = Literal[
    "proof_gap",
    "bad_generalization",
    "numeric_artifact",
    "undefined_term",
    "overclaim",
    "missing_baseline",
    "circular_dependency",
    "bad_compression",
]


@dataclass(frozen=True)
class NegativeMemoryEntry:
    id: str
    failure_type: FailureType
    lesson: str
    trigger_phrase: str
    replacement_rule: str
    counterexample: str = ""
    branch: str = "general"

    def matches(self, text: str) -> bool:
        """Return True when text contains the trigger phrase."""
        return self.trigger_phrase.lower() in text.lower()


@dataclass
class NegativeMemoryBank:
    entries: dict[str, NegativeMemoryEntry] = field(default_factory=dict)

    def add(self, entry: NegativeMemoryEntry) -> None:
        if entry.id in self.entries:
            raise ValueError(f"negative memory entry already exists: {entry.id}")
        self.entries[entry.id] = entry

    def scan(self, text: str) -> list[NegativeMemoryEntry]:
        return [entry for entry in self.entries.values() if entry.matches(text)]

    def risk_score(self, text: str) -> float:
        """Return a simple score in [0, 1] based on matched anti-patterns."""
        if not self.entries:
            return 0.0
        return min(1.0, len(self.scan(text)) / max(1, len(self.entries)))

    def replacement_rules_for(self, text: str) -> list[str]:
        return [entry.replacement_rule for entry in self.scan(text)]

    def by_failure_type(self, failure_type: FailureType) -> list[NegativeMemoryEntry]:
        return [entry for entry in self.entries.values() if entry.failure_type == failure_type]


def default_negative_memory_bank() -> NegativeMemoryBank:
    """Return default anti-illusion motifs for the Tristan canon."""
    bank = NegativeMemoryBank()
    defaults = [
        NegativeMemoryEntry(
            id="NM-001",
            failure_type="overclaim",
            lesson="Fertility is not truth.",
            trigger_phrase="it is proven",
            replacement_rule="Keep as conjecture unless a proof or robust validation is attached.",
        ),
        NegativeMemoryEntry(
            id="NM-002",
            failure_type="numeric_artifact",
            lesson="A numerical pattern can be caused by sampling, leakage or a weak baseline.",
            trigger_phrase="the experiment proves",
            replacement_rule="Require baseline, validation split and counterexample search.",
        ),
        NegativeMemoryEntry(
            id="NM-003",
            failure_type="undefined_term",
            lesson="A named object must have a definition before promotion.",
            trigger_phrase="revolutionary object",
            replacement_rule="Add definition, hypotheses, examples and non-examples.",
        ),
        NegativeMemoryEntry(
            id="NM-004",
            failure_type="bad_generalization",
            lesson="A generalization must preserve hypotheses.",
            trigger_phrase="works for everything",
            replacement_rule="State the domain, counter-domain and known failure modes.",
        ),
        NegativeMemoryEntry(
            id="NM-005",
            failure_type="missing_baseline",
            lesson="Performance claims need comparison.",
            trigger_phrase="improves performance",
            replacement_rule="Attach baselines, metrics, validation split and ablations.",
        ),
    ]
    for entry in defaults:
        bank.add(entry)
    return bank


def filter_claims_by_negative_memory(claims: Iterable[str], bank: NegativeMemoryBank | None = None) -> list[tuple[str, float, list[str]]]:
    """Return `(claim, score, replacement_rules)` for each claim."""
    active_bank = bank or default_negative_memory_bank()
    return [(claim, active_bank.risk_score(claim), active_bank.replacement_rules_for(claim)) for claim in claims]
