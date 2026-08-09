from __future__ import annotations

import itertools
import json
import math
import statistics
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .simulation import AgentGenome, ArenaConfig, MatchResult, run_arena_t0


@dataclass(frozen=True)
class RatingVector:
    agent_id: str
    wins: int
    draws: int
    losses: int
    score_for: float
    score_against: float
    robustness: float
    efficiency: float
    novelty: float
    stability: float

    @property
    def points(self) -> float:
        return self.wins + 0.5 * self.draws

    @property
    def score_delta(self) -> float:
        return self.score_for - self.score_against

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["points"] = round(self.points, 6)
        data["score_delta"] = round(self.score_delta, 6)
        return data


@dataclass(frozen=True)
class TournamentReport:
    seeds: tuple[int, ...]
    mirrored: bool
    ratings: tuple[RatingVector, ...]
    matches: tuple[MatchResult, ...]

    def ranking(self) -> tuple[RatingVector, ...]:
        return tuple(sorted(self.ratings, key=lambda r: (r.points, r.score_delta, r.robustness, r.novelty, r.agent_id), reverse=True))

    def to_dict(self, *, include_replays: bool = False) -> dict[str, Any]:
        return {
            "seeds": list(self.seeds),
            "mirrored": self.mirrored,
            "match_count": len(self.matches),
            "ratings": [rating.to_dict() for rating in self.ranking()],
            "matches": [match.to_dict(include_replay=include_replays) for match in self.matches],
        }

    def to_json(self, *, include_replays: bool = False) -> str:
        return json.dumps(self.to_dict(include_replays=include_replays), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def run_round_robin(
    population: Iterable[AgentGenome],
    *,
    seeds: Iterable[int] = (0, 1, 2),
    config: ArenaConfig | None = None,
    mirrored: bool = True,
) -> TournamentReport:
    agents = tuple(genome.normalized() for genome in population)
    seed_tuple = tuple(int(seed) for seed in seeds)
    if len(agents) < 2:
        raise ValueError("tournament needs at least two agents")
    if len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("agent IDs must be unique")
    if not seed_tuple:
        raise ValueError("at least one seed is required")

    config = config or ArenaConfig()
    matches: list[MatchResult] = []
    stats: dict[str, dict[str, Any]] = {
        agent.agent_id: {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "score_for": 0.0,
            "score_against": 0.0,
            "efficiencies": [],
            "scores": [],
        }
        for agent in agents
    }

    for first, second in itertools.combinations(agents, 2):
        orientations = ((first, second), (second, first)) if mirrored else ((first, second),)
        for seed in seed_tuple:
            for left, right in orientations:
                result = run_arena_t0(left, right, seed=seed, config=config)
                matches.append(result)
                _accumulate(stats, result)

    descriptors = {agent.agent_id: agent.descriptor() for agent in agents}
    ratings = tuple(_rating(agent.agent_id, stats[agent.agent_id], descriptors) for agent in agents)
    return TournamentReport(seeds=seed_tuple, mirrored=mirrored, ratings=ratings, matches=tuple(matches))


def _accumulate(stats: dict[str, dict[str, Any]], match: MatchResult) -> None:
    left_id, right_id = match.left.agent_id, match.right.agent_id
    left_score = float(match.metrics[left_id]["score"])
    right_score = float(match.metrics[right_id]["score"])
    stats[left_id]["score_for"] += left_score
    stats[left_id]["score_against"] += right_score
    stats[right_id]["score_for"] += right_score
    stats[right_id]["score_against"] += left_score
    stats[left_id]["efficiencies"].append(float(match.metrics[left_id]["efficiency"]))
    stats[right_id]["efficiencies"].append(float(match.metrics[right_id]["efficiency"]))
    stats[left_id]["scores"].append(left_score)
    stats[right_id]["scores"].append(right_score)

    if match.winner is None:
        stats[left_id]["draws"] += 1
        stats[right_id]["draws"] += 1
    else:
        loser = right_id if match.winner == left_id else left_id
        stats[match.winner]["wins"] += 1
        stats[loser]["losses"] += 1


def _rating(agent_id: str, stat: dict[str, Any], descriptors: dict[str, tuple[float, ...]]) -> RatingVector:
    total = stat["wins"] + stat["draws"] + stat["losses"]
    robustness = (stat["wins"] + 0.5 * stat["draws"]) / max(1, total)
    efficiency = statistics.fmean(stat["efficiencies"]) if stat["efficiencies"] else 0.0
    spread = statistics.pstdev(stat["scores"]) if len(stat["scores"]) > 1 else 0.0
    stability = 1.0 / (1.0 + spread)
    novelty = _novelty(agent_id, descriptors)
    return RatingVector(
        agent_id=agent_id,
        wins=int(stat["wins"]),
        draws=int(stat["draws"]),
        losses=int(stat["losses"]),
        score_for=round(float(stat["score_for"]), 6),
        score_against=round(float(stat["score_against"]), 6),
        robustness=round(robustness, 6),
        efficiency=round(efficiency, 6),
        novelty=round(novelty, 6),
        stability=round(stability, 6),
    )


def _novelty(agent_id: str, descriptors: dict[str, tuple[float, ...]]) -> float:
    origin = descriptors[agent_id]
    distances = []
    for other_id, other in descriptors.items():
        if other_id == agent_id:
            continue
        distances.append(math.sqrt(sum((a - b) ** 2 for a, b in zip(origin, other))))
    return statistics.fmean(distances) if distances else 0.0
