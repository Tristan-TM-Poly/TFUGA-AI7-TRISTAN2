from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .simulation import AgentGenome, ArenaConfig
from .tournament import RatingVector, TournamentReport, run_round_robin


_ALLOWED_AXES = ("seek_resource", "aggression", "conservation", "exploration")


@dataclass(frozen=True)
class ArchiveConfig:
    axes: tuple[str, ...] = ("aggression", "exploration")
    bins: tuple[int, ...] = (8, 8)
    novelty_k: int = 5

    def validate(self) -> None:
        if not self.axes:
            raise ValueError("axes cannot be empty")
        if len(self.axes) != len(self.bins):
            raise ValueError("axes and bins must have equal length")
        if len(set(self.axes)) != len(self.axes):
            raise ValueError("axes must be unique")
        if any(axis not in _ALLOWED_AXES for axis in self.axes):
            raise ValueError(f"axes must be selected from {_ALLOWED_AXES}")
        if any(bin_count < 2 for bin_count in self.bins):
            raise ValueError("each axis must have at least two bins")
        if self.novelty_k < 1:
            raise ValueError("novelty_k must be >= 1")

    @property
    def cell_count(self) -> int:
        result = 1
        for bin_count in self.bins:
            result *= bin_count
        return result


@dataclass(frozen=True)
class BehaviorDescriptor:
    axes: tuple[str, ...]
    values: tuple[float, ...]

    @classmethod
    def from_genome(cls, genome: AgentGenome, axes: tuple[str, ...]) -> "BehaviorDescriptor":
        normalized = genome.normalized()
        values = tuple(float(getattr(normalized, axis)) for axis in axes)
        return cls(axes=axes, values=values)

    def to_dict(self) -> dict[str, Any]:
        return {"axes": list(self.axes), "values": list(self.values)}


@dataclass(frozen=True)
class EliteRecord:
    cell: tuple[int, ...]
    agent: AgentGenome
    descriptor: BehaviorDescriptor
    quality: float
    rating: RatingVector

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell": list(self.cell),
            "agent": asdict(self.agent),
            "descriptor": self.descriptor.to_dict(),
            "quality": self.quality,
            "rating": self.rating.to_dict(),
        }


@dataclass(frozen=True)
class QualityDiversityReport:
    config: ArchiveConfig
    elites: tuple[EliteRecord, ...]
    coverage: float
    qd_score: float
    mean_quality: float
    mean_novelty: float
    max_quality: float
    occupied_cells: int
    total_cells: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "coverage": self.coverage,
            "qd_score": self.qd_score,
            "mean_quality": self.mean_quality,
            "mean_novelty": self.mean_novelty,
            "max_quality": self.max_quality,
            "occupied_cells": self.occupied_cells,
            "total_cells": self.total_cells,
            "elites": [elite.to_dict() for elite in self.elites],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class QualityDiversityExperiment:
    tournament: TournamentReport
    report: QualityDiversityReport

    def to_dict(self, *, include_matches: bool = False) -> dict[str, Any]:
        return {
            "tournament": self.tournament.to_dict(include_replays=include_matches),
            "quality_diversity": self.report.to_dict(),
        }

    def to_json(self, *, include_matches: bool = False) -> str:
        return json.dumps(
            self.to_dict(include_matches=include_matches),
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        ) + "\n"


class MapElitesArchive:
    """Deterministic MAP-Elites style archive over bounded genome descriptors."""

    def __init__(self, config: ArchiveConfig | None = None) -> None:
        self.config = config or ArchiveConfig()
        self.config.validate()
        self._cells: dict[tuple[int, ...], EliteRecord] = {}

    def descriptor(self, genome: AgentGenome) -> BehaviorDescriptor:
        return BehaviorDescriptor.from_genome(genome, self.config.axes)

    def cell_for(self, descriptor: BehaviorDescriptor) -> tuple[int, ...]:
        if descriptor.axes != self.config.axes:
            raise ValueError("descriptor axes do not match archive axes")
        if len(descriptor.values) != len(self.config.bins):
            raise ValueError("descriptor dimensionality mismatch")
        cell: list[int] = []
        for value, bin_count in zip(descriptor.values, self.config.bins):
            bounded = max(0.0, min(1.0, float(value)))
            index = min(bin_count - 1, int(bounded * bin_count))
            cell.append(index)
        return tuple(cell)

    def insert(self, genome: AgentGenome, rating: RatingVector, *, quality: float | None = None) -> bool:
        if genome.agent_id != rating.agent_id:
            raise ValueError("genome and rating agent IDs must match")
        descriptor = self.descriptor(genome)
        cell = self.cell_for(descriptor)
        score = round(float(quality if quality is not None else quality_from_rating(rating)), 6)
        candidate = EliteRecord(cell=cell, agent=genome.normalized(), descriptor=descriptor, quality=score, rating=rating)
        current = self._cells.get(cell)
        if current is None or score > current.quality or (score == current.quality and genome.agent_id < current.agent.agent_id):
            self._cells[cell] = candidate
            return True
        return False

    def elites(self) -> tuple[EliteRecord, ...]:
        return tuple(self._cells[cell] for cell in sorted(self._cells))

    def novelty(self, descriptor: BehaviorDescriptor, *, exclude_agent_id: str | None = None) -> float:
        distances: list[float] = []
        dimension_scale = math.sqrt(max(1, len(descriptor.values)))
        for elite in self._cells.values():
            if exclude_agent_id is not None and elite.agent.agent_id == exclude_agent_id:
                continue
            distance = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(descriptor.values, elite.descriptor.values))
            ) / dimension_scale
            distances.append(distance)
        if not distances:
            return 0.0
        distances.sort()
        k = min(self.config.novelty_k, len(distances))
        return round(statistics.fmean(distances[:k]), 6)

    def report(self) -> QualityDiversityReport:
        elites = self.elites()
        qualities = [elite.quality for elite in elites]
        novelties = [self.novelty(elite.descriptor, exclude_agent_id=elite.agent.agent_id) for elite in elites]
        occupied = len(elites)
        total = self.config.cell_count
        coverage = occupied / total
        qd_score = sum(max(0.0, quality) for quality in qualities)
        return QualityDiversityReport(
            config=self.config,
            elites=elites,
            coverage=round(coverage, 6),
            qd_score=round(qd_score, 6),
            mean_quality=round(statistics.fmean(qualities), 6) if qualities else 0.0,
            mean_novelty=round(statistics.fmean(novelties), 6) if novelties else 0.0,
            max_quality=round(max(qualities), 6) if qualities else 0.0,
            occupied_cells=occupied,
            total_cells=total,
        )


def quality_from_rating(rating: RatingVector) -> float:
    """Bounded-complexity scalar used only to select an elite inside one cell."""

    return round(
        rating.points
        + 0.01 * rating.score_delta
        + 0.50 * rating.robustness
        + 0.05 * rating.efficiency
        + 0.25 * rating.stability,
        6,
    )


def build_map_elites(
    population: Iterable[AgentGenome],
    tournament: TournamentReport,
    *,
    config: ArchiveConfig | None = None,
) -> MapElitesArchive:
    agents = tuple(agent.normalized() for agent in population)
    if len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("agent IDs must be unique")
    rating_by_id = {rating.agent_id: rating for rating in tournament.ratings}
    if set(rating_by_id) != {agent.agent_id for agent in agents}:
        raise ValueError("tournament ratings must exactly cover the population")

    archive = MapElitesArchive(config)
    for agent in sorted(agents, key=lambda item: item.agent_id):
        archive.insert(agent, rating_by_id[agent.agent_id])
    return archive


def run_quality_diversity(
    population: Iterable[AgentGenome],
    *,
    seeds: Iterable[int] = (0, 1, 2),
    arena_config: ArenaConfig | None = None,
    archive_config: ArchiveConfig | None = None,
) -> QualityDiversityExperiment:
    agents = tuple(agent.normalized() for agent in population)
    tournament = run_round_robin(agents, seeds=seeds, config=arena_config, mirrored=True)
    archive = build_map_elites(agents, tournament, config=archive_config)
    return QualityDiversityExperiment(tournament=tournament, report=archive.report())
