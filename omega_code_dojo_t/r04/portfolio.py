from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .families import FAMILIES, ProblemFamily
from .hashing import sha256_hex
from .models import ProblemInstance, ResolutionPolicy


@dataclass(frozen=True)
class ProblemPortfolio:
    families: tuple[ProblemFamily, ...] = FAMILIES
    seed_cardinality: int = 2**32
    difficulty_cardinality: int = 32

    @property
    def logical_problem_space(self) -> int:
        return len(self.families) * self.seed_cardinality * self.difficulty_cardinality

    def materialize(self, policy: ResolutionPolicy) -> Iterator[ProblemInstance]:
        family_count = len(self.families)
        start = int(sha256_hex(policy.to_dict())[:16], 16) % self.seed_cardinality
        stride = 2_654_435_761
        for ordinal in range(policy.problem_budget):
            family = self.families[ordinal % family_count]
            round_index = ordinal // family_count
            seed = (start + round_index * stride + ordinal * 97) % self.seed_cardinality
            difficulty = 1 + (ordinal % min(policy.difficulty_cycle, self.difficulty_cardinality))
            yield family.generate(seed, difficulty)

    def catalog(self) -> list[dict[str, object]]:
        return [
            {
                "family_id": family.family_id,
                "domain": family.domain,
                "title": family.title,
                "strategies": [strategy.to_dict() for strategy in family.strategies],
                "invariants": list(family.invariants),
            }
            for family in self.families
        ]


DEFAULT_PORTFOLIO = ProblemPortfolio()
