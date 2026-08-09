from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .quality_diversity import quality_from_rating
from .simulation import AgentGenome, ArenaConfig, run_arena_t0
from .tournament import RatingVector, TournamentReport
from .verification import FuzzReport


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    polarity: str
    category: str
    payload: dict[str, Any]
    evidence_hash: str

    @classmethod
    def create(cls, polarity: str, category: str, payload: dict[str, Any]) -> "MemoryRecord":
        if polarity not in {"plus", "minus"}:
            raise ValueError("polarity must be plus or minus")
        if not category:
            raise ValueError("category cannot be empty")
        evidence_hash = _canonical_hash(payload)
        memory_id = f"m{polarity[0]}-{category}-{evidence_hash[:16]}"
        return cls(memory_id, polarity, category, dict(payload), evidence_hash)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChampionRecord:
    generation: int
    rank: int
    agent: AgentGenome
    rating: RatingVector
    quality: float
    tournament_seeds: tuple[int, ...]
    receipt_hash: str

    @classmethod
    def create(
        cls,
        *,
        generation: int,
        rank: int,
        agent: AgentGenome,
        rating: RatingVector,
        tournament_seeds: tuple[int, ...],
    ) -> "ChampionRecord":
        if generation < 0:
            raise ValueError("generation must be >= 0")
        if rank < 1:
            raise ValueError("rank must be >= 1")
        if agent.agent_id != rating.agent_id:
            raise ValueError("agent and rating IDs must match")
        payload = {
            "generation": generation,
            "rank": rank,
            "agent": asdict(agent.normalized()),
            "rating": rating.to_dict(),
            "tournament_seeds": list(tournament_seeds),
        }
        return cls(
            generation=generation,
            rank=rank,
            agent=agent.normalized(),
            rating=rating,
            quality=quality_from_rating(rating),
            tournament_seeds=tournament_seeds,
            receipt_hash=_canonical_hash(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "rank": self.rank,
            "agent": asdict(self.agent),
            "rating": self.rating.to_dict(),
            "quality": self.quality,
            "tournament_seeds": list(self.tournament_seeds),
            "receipt_hash": self.receipt_hash,
        }


@dataclass
class HallOfFame:
    _records: dict[str, ChampionRecord] = field(default_factory=dict)

    def admit(
        self,
        population: Iterable[AgentGenome],
        tournament: TournamentReport,
        *,
        generation: int,
        top_k: int = 3,
    ) -> tuple[ChampionRecord, ...]:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        agents = {agent.agent_id: agent.normalized() for agent in population}
        if len(agents) < 2:
            raise ValueError("population must contain at least two unique agents")
        ranking = tournament.ranking()
        if set(agents) != {rating.agent_id for rating in tournament.ratings}:
            raise ValueError("tournament ratings must exactly cover population")

        admitted: list[ChampionRecord] = []
        for rank, rating in enumerate(ranking[: min(top_k, len(ranking))], start=1):
            record = ChampionRecord.create(
                generation=generation,
                rank=rank,
                agent=agents[rating.agent_id],
                rating=rating,
                tournament_seeds=tournament.seeds,
            )
            self._records.setdefault(record.receipt_hash, record)
            admitted.append(record)
        return tuple(admitted)

    def records(self) -> tuple[ChampionRecord, ...]:
        return tuple(
            sorted(
                self._records.values(),
                key=lambda record: (record.generation, record.rank, record.agent.agent_id, record.receipt_hash),
            )
        )

    def challenge_agents(self, *, limit: int | None = None) -> tuple[AgentGenome, ...]:
        records = sorted(
            self._records.values(),
            key=lambda record: (record.generation, -record.rank, record.quality, record.agent.agent_id),
            reverse=True,
        )
        unique: list[AgentGenome] = []
        seen: set[str] = set()
        for record in records:
            if record.agent.agent_id in seen:
                continue
            seen.add(record.agent.agent_id)
            unique.append(record.agent)
            if limit is not None and len(unique) >= limit:
                break
        return tuple(unique)

    def to_dict(self) -> dict[str, Any]:
        return {"records": [record.to_dict() for record in self.records()]}


@dataclass
class EvolutionaryMemory:
    hall_of_fame: HallOfFame = field(default_factory=HallOfFame)
    plus: dict[str, MemoryRecord] = field(default_factory=dict)
    minus: dict[str, MemoryRecord] = field(default_factory=dict)

    def admit_tournament(
        self,
        population: Iterable[AgentGenome],
        tournament: TournamentReport,
        *,
        generation: int,
        top_k: int = 3,
    ) -> tuple[ChampionRecord, ...]:
        records = self.hall_of_fame.admit(population, tournament, generation=generation, top_k=top_k)
        for record in records:
            memory = MemoryRecord.create(
                "plus",
                "champion",
                {
                    "generation": record.generation,
                    "rank": record.rank,
                    "agent_id": record.agent.agent_id,
                    "quality": record.quality,
                    "receipt_hash": record.receipt_hash,
                },
            )
            self.plus.setdefault(memory.memory_id, memory)
        return records

    def record_plus(self, category: str, payload: dict[str, Any]) -> MemoryRecord:
        record = MemoryRecord.create("plus", category, payload)
        self.plus.setdefault(record.memory_id, record)
        return record

    def record_minus(self, category: str, payload: dict[str, Any]) -> MemoryRecord:
        record = MemoryRecord.create("minus", category, payload)
        self.minus.setdefault(record.memory_id, record)
        return record

    def ingest_fuzz_report(self, report: FuzzReport) -> tuple[MemoryRecord, ...]:
        records: list[MemoryRecord] = []
        for failure in report.failures:
            record = self.record_minus(
                "fuzz_failure",
                {
                    "campaign_seed": report.seed,
                    "case_index": failure.case_index,
                    "case_seed": failure.seed,
                    "flags": list(failure.flags),
                },
            )
            records.append(record)
        return tuple(records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hall_of_fame": self.hall_of_fame.to_dict(),
            "m_plus": [self.plus[key].to_dict() for key in sorted(self.plus)],
            "m_minus": [self.minus[key].to_dict() for key in sorted(self.minus)],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class RegressionResult:
    champion_id: str
    seeds: tuple[int, ...]
    match_count: int
    candidate_points: float
    available_points: float
    score_fraction: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AntiForgettingReport:
    candidate_id: str
    threshold: float
    results: tuple[RegressionResult, ...]
    total_points: float
    total_available_points: float
    score_fraction: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "threshold": self.threshold,
            "results": [result.to_dict() for result in self.results],
            "total_points": self.total_points,
            "total_available_points": self.total_available_points,
            "score_fraction": self.score_fraction,
            "passed": self.passed,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def evaluate_anti_forgetting(
    candidate: AgentGenome,
    hall_of_fame: HallOfFame,
    *,
    seeds: Iterable[int] = (0, 1, 2),
    config: ArenaConfig | None = None,
    threshold: float = 0.50,
    champion_limit: int | None = None,
) -> AntiForgettingReport:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple:
        raise ValueError("at least one seed is required")

    config = config or ArenaConfig()
    candidate = candidate.normalized()
    champions = tuple(
        champion
        for champion in hall_of_fame.challenge_agents(limit=None)
        if champion.agent_id != candidate.agent_id
    )
    if champion_limit is not None:
        if champion_limit < 1:
            raise ValueError("champion_limit must be >= 1 when provided")
        champions = champions[:champion_limit]
    if not champions:
        raise ValueError("Hall of Fame has no distinct challenge agent for candidate")

    results: list[RegressionResult] = []
    total_points = 0.0
    total_available = 0.0

    for champion in champions:
        points = 0.0
        matches = 0
        for seed in seed_tuple:
            for left, right in ((candidate, champion), (champion, candidate)):
                match = run_arena_t0(left, right, seed=seed, config=config)
                matches += 1
                if match.winner is None:
                    points += 0.5
                elif match.winner == candidate.agent_id:
                    points += 1.0
        available = float(matches)
        fraction = points / available if available else 0.0
        results.append(
            RegressionResult(
                champion_id=champion.agent_id,
                seeds=seed_tuple,
                match_count=matches,
                candidate_points=round(points, 6),
                available_points=available,
                score_fraction=round(fraction, 6),
            )
        )
        total_points += points
        total_available += available

    fraction = total_points / total_available if total_available else 0.0
    return AntiForgettingReport(
        candidate_id=candidate.agent_id,
        threshold=threshold,
        results=tuple(results),
        total_points=round(total_points, 6),
        total_available_points=round(total_available, 6),
        score_fraction=round(fraction, 6),
        passed=fraction >= threshold,
    )
