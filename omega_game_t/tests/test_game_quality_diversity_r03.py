from __future__ import annotations

from omega_game.engines.evolution import seed_population
from omega_game.engines.quality_diversity import (
    ArchiveConfig,
    BehaviorDescriptor,
    MapElitesArchive,
    build_map_elites,
    quality_from_rating,
    run_quality_diversity,
)
from omega_game.engines.simulation import AgentGenome, ArenaConfig
from omega_game.engines.tournament import RatingVector, run_round_robin


def _rating(agent_id: str, *, wins: int = 1, score_delta: float = 0.0) -> RatingVector:
    score_for = 10.0 + max(0.0, score_delta)
    score_against = 10.0 + max(0.0, -score_delta)
    return RatingVector(
        agent_id=agent_id,
        wins=wins,
        draws=0,
        losses=0,
        score_for=score_for,
        score_against=score_against,
        robustness=1.0,
        efficiency=1.0,
        novelty=0.0,
        stability=1.0,
    )


def test_archive_config_and_cells_are_bounded() -> None:
    archive = MapElitesArchive(ArchiveConfig(axes=("aggression", "exploration"), bins=(4, 5)))
    low = BehaviorDescriptor(("aggression", "exploration"), (0.0, 0.0))
    high = BehaviorDescriptor(("aggression", "exploration"), (1.0, 1.0))
    assert archive.cell_for(low) == (0, 0)
    assert archive.cell_for(high) == (3, 4)
    assert archive.config.cell_count == 20


def test_archive_replaces_only_with_better_cell_elite() -> None:
    archive = MapElitesArchive(ArchiveConfig(bins=(4, 4)))
    a = AgentGenome("a", aggression=0.3, exploration=0.3, seek_resource=0.1)
    b = AgentGenome("b", aggression=0.3, exploration=0.3, seek_resource=0.9)
    assert archive.insert(a, _rating("a"), quality=1.0)
    assert not archive.insert(b, _rating("b"), quality=0.5)
    assert archive.elites()[0].agent.agent_id == "a"
    assert archive.insert(b, _rating("b"), quality=2.0)
    assert archive.elites()[0].agent.agent_id == "b"


def test_archive_tie_break_is_deterministic() -> None:
    archive = MapElitesArchive(ArchiveConfig(bins=(4, 4)))
    z = AgentGenome("z", aggression=0.2, exploration=0.2)
    a = AgentGenome("a", aggression=0.2, exploration=0.2)
    archive.insert(z, _rating("z"), quality=1.0)
    archive.insert(a, _rating("a"), quality=1.0)
    assert archive.elites()[0].agent.agent_id == "a"


def test_novelty_is_normalized_and_nonzero_for_distinct_cells() -> None:
    archive = MapElitesArchive(ArchiveConfig(bins=(4, 4), novelty_k=2))
    a = AgentGenome("a", aggression=0.0, exploration=0.0)
    b = AgentGenome("b", aggression=1.0, exploration=1.0)
    archive.insert(a, _rating("a"), quality=1.0)
    archive.insert(b, _rating("b"), quality=1.0)
    novelty = archive.novelty(archive.descriptor(a), exclude_agent_id="a")
    assert novelty == 1.0


def test_quality_from_rating_rewards_performance_terms() -> None:
    weak = _rating("weak", wins=0, score_delta=-5.0)
    strong = _rating("strong", wins=3, score_delta=5.0)
    assert quality_from_rating(strong) > quality_from_rating(weak)


def test_build_map_elites_uses_tournament_population_contract() -> None:
    population = seed_population(4, seed=4)
    tournament = run_round_robin(population, seeds=(1,), config=ArenaConfig(max_steps=8), mirrored=True)
    archive = build_map_elites(population, tournament, config=ArchiveConfig(bins=(4, 4)))
    report = archive.report()
    assert 1 <= report.occupied_cells <= 4
    assert report.total_cells == 16
    assert 0.0 < report.coverage <= 0.25
    assert report.qd_score >= 0.0


def test_quality_diversity_experiment_is_deterministic() -> None:
    population = seed_population(5, seed=11)
    kwargs = {
        "seeds": (3, 4),
        "arena_config": ArenaConfig(max_steps=12),
        "archive_config": ArchiveConfig(bins=(5, 5), novelty_k=3),
    }
    a = run_quality_diversity(population, **kwargs)
    b = run_quality_diversity(population, **kwargs)
    assert a.to_json(include_matches=False) == b.to_json(include_matches=False)


def test_invalid_archive_config_fails_closed() -> None:
    for config in (
        ArchiveConfig(axes=(), bins=()),
        ArchiveConfig(axes=("aggression",), bins=(4, 4)),
        ArchiveConfig(axes=("unknown",), bins=(4,)),
        ArchiveConfig(axes=("aggression",), bins=(1,)),
    ):
        try:
            MapElitesArchive(config)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid config should fail: {config}")
