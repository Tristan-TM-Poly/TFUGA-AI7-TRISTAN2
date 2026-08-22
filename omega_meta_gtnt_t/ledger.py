from __future__ import annotations

from dataclasses import dataclass, field

from .models import ClaimRecord, StrategyPath, TruthLevel


@dataclass(frozen=True)
class NoGoRule:
    problem_family: str
    representation: str
    reason: str
    path_signature: str | None = None

    def matches(self, path: StrategyPath) -> bool:
        if self.problem_family not in {"*", path.problem_family}:
            return False
        if self.representation not in {"*", path.representation}:
            return False
        return self.path_signature in {None, "*", path.signature}


@dataclass
class NegativeMemory:
    rules: list[NoGoRule] = field(default_factory=list)

    def remember(self, rule: NoGoRule) -> None:
        if rule not in self.rules:
            self.rules.append(rule)

    def blocked_reason(self, path: StrategyPath) -> str | None:
        for rule in self.rules:
            if rule.matches(path):
                return rule.reason
        return None

    def prune(self, paths: list[StrategyPath]) -> tuple[list[StrategyPath], dict[str, str]]:
        kept: list[StrategyPath] = []
        rejected: dict[str, str] = {}
        for path in paths:
            reason = self.blocked_reason(path)
            if reason is None:
                kept.append(path)
            else:
                rejected[path.signature] = reason
        return kept, rejected


@dataclass
class EpistemicLedger:
    records: list[ClaimRecord] = field(default_factory=list)

    def append(self, record: ClaimRecord) -> None:
        self.records.append(record)

    @staticmethod
    def can_promote(record: ClaimRecord, target: TruthLevel) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if target <= record.level:
            return True, ("already_at_or_above_target",)
        if not record.evidence:
            reasons.append("missing_evidence")
        if target >= TruthLevel.COUNTERTEST_ROBUST and not record.countertests:
            reasons.append("missing_countertests")
        if target >= TruthLevel.KERNEL_VERIFIED and not record.kernel_verified:
            reasons.append("missing_kernel_verification")
        if target >= TruthLevel.INDEPENDENTLY_REPLICATED and record.independent_replications < 1:
            reasons.append("missing_independent_replication")
        if target == TruthLevel.ESTABLISHED_IN_DOMAIN:
            reasons.append("domain_establishment_requires_external_scientific_consensus")
        return not reasons, tuple(reasons)
