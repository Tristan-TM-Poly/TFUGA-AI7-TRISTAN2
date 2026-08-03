from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .hashing import sha256_hex
from .models import CandidateUtility, FrontierCell, SkillPosterior


@dataclass
class SkillGraph:
    posteriors: dict[str, SkillPosterior] = field(default_factory=dict)

    def get(self, skill_id: str) -> SkillPosterior:
        return self.posteriors.get(skill_id, SkillPosterior(skill_id))

    def observe(self, skill_id: str, success: bool, weight: float = 1.0) -> None:
        self.posteriors[skill_id] = self.get(skill_id).observe(success, weight)

    def snapshot(self) -> tuple[SkillPosterior, ...]:
        return tuple(self.posteriors[key] for key in sorted(self.posteriors))


@dataclass(frozen=True)
class UtilityWeights:
    information_gain: float = 1.0
    weakness: float = 0.8
    transfer: float = 0.5
    novelty: float = 0.7
    cost: float = 0.4
    risk: float = 1.2


class ActiveCurriculum:
    def __init__(
        self,
        skills: SkillGraph | None = None,
        weights: UtilityWeights = UtilityWeights(),
    ) -> None:
        self.skills = skills or SkillGraph()
        self.weights = weights

    def utility(
        self,
        cell: FrontierCell,
        seen_addresses: set[str],
        risk_overrides: Mapping[str, float] | None = None,
    ) -> CandidateUtility:
        domain = self.skills.get(f"domain:{cell.domain}")
        language = self.skills.get(f"language:{cell.language}")
        mutation = self.skills.get(f"mutation:{cell.mutation_family}")
        uncertainty = (domain.uncertainty + language.uncertainty + mutation.uncertainty) / 3
        mastery = (domain.mean + language.mean + mutation.mean) / 3
        information_gain = min(1.0, uncertainty * 4.0)
        weakness = 1.0 - mastery
        transfer = _stable_fraction("transfer", cell.domain, cell.archetype)
        novelty = 0.0 if cell.address in seen_addresses else 1.0
        cost = 0.2 + 0.8 * _stable_fraction("cost", cell.language, cell.execution_regime)
        risk = (risk_overrides or {}).get(
            cell.address,
            0.1 * _stable_fraction("risk", cell.domain, cell.mutation_family),
        )
        total = (
            self.weights.information_gain * information_gain
            + self.weights.weakness * weakness
            + self.weights.transfer * transfer
            + self.weights.novelty * novelty
            - self.weights.cost * cost
            - self.weights.risk * risk
        )
        return CandidateUtility(
            address=cell.address,
            information_gain=information_gain,
            weakness=weakness,
            transfer=transfer,
            novelty=novelty,
            cost=cost,
            risk=risk,
            total=total,
        )

    def rank(
        self,
        candidates: Iterable[FrontierCell],
        seen_addresses: set[str],
        limit: int,
    ) -> tuple[tuple[FrontierCell, CandidateUtility], ...]:
        if limit <= 0:
            return ()
        scored = [
            (cell, self.utility(cell, seen_addresses)) for cell in candidates
        ]
        scored.sort(key=lambda item: (-item[1].total, item[0].address))
        return tuple(scored[:limit])

    def update_from_outcome(
        self,
        cell: FrontierCell,
        success: bool,
        mutation_score: float,
    ) -> None:
        base_weight = 0.5 + max(0.0, min(1.0, mutation_score))
        self.skills.observe(f"domain:{cell.domain}", success, base_weight)
        self.skills.observe(f"language:{cell.language}", success, base_weight)
        self.skills.observe(
            f"mutation:{cell.mutation_family}",
            success and mutation_score >= 0.8,
            base_weight,
        )


def _stable_fraction(*parts: str) -> float:
    digest = sha256_hex(list(parts))
    return int(digest[:12], 16) / float(16**12 - 1)
