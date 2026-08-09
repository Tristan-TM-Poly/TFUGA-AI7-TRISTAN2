from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .engines import (
    AgentGenome,
    ArchiveConfig,
    ArenaConfig,
    EvolutionConfig,
    EvolutionaryMemory,
    GameSpecCompiler,
    audit_match,
    evaluate_anti_forgetting,
    evolve,
    evolve_environments,
    fuzz_arena_t0,
    run_arena_t0,
    run_coevolution_cycle,
    run_quality_diversity,
    run_round_robin,
    run_sparse_benchmark,
    seed_environments,
    seed_population,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-game", description="Omega GAME-SIM-EVO deterministic research lab")
    sub = parser.add_subparsers(dest="command", required=True)

    arena = sub.add_parser("arena", help="run one deterministic Arena-T0 match")
    arena.add_argument("--seed", type=int, default=0)
    arena.add_argument("--steps", type=int, default=96)

    tournament = sub.add_parser("tournament", help="run a mirrored round-robin tournament")
    tournament.add_argument("--seed", type=int, default=0)
    tournament.add_argument("--population", type=int, default=6)
    tournament.add_argument("--steps", type=int, default=64)

    evo = sub.add_parser("evolve", help="evolve an Arena-T0 population")
    evo.add_argument("--seed", type=int, default=0)
    evo.add_argument("--population", type=int, default=8)
    evo.add_argument("--generations", type=int, default=2)
    evo.add_argument("--steps", type=int, default=48)

    qd = sub.add_parser("quality-diversity", help="run MAP-Elites quality-diversity analysis")
    qd.add_argument("--seed", type=int, default=0)
    qd.add_argument("--population", type=int, default=8)
    qd.add_argument("--steps", type=int, default=48)
    qd.add_argument("--bins", type=int, default=8)

    memory = sub.add_parser("memory-demo", help="build Hall of Fame and run anti-forgetting regression")
    memory.add_argument("--seed", type=int, default=0)
    memory.add_argument("--population", type=int, default=6)
    memory.add_argument("--top-k", type=int, default=2)
    memory.add_argument("--steps", type=int, default=32)
    memory.add_argument("--threshold", type=float, default=0.50)

    coevo = sub.add_parser("coevolve", help="evaluate agents across train/held-out environment seeds")
    coevo.add_argument("--seed", type=int, default=0)
    coevo.add_argument("--population", type=int, default=6)
    coevo.add_argument("--environments", type=int, default=4)
    coevo.add_argument("--adversarial-limit", type=int, default=2)
    coevo.add_argument("--next-environments", type=int, default=4)

    compile_spec = sub.add_parser("compile-spec", help="compile a bounded JSON GameSpec into Omega GAME primitives")
    compile_spec.add_argument("path")
    compile_spec.add_argument("--seed", type=int, default=0)
    compile_spec.add_argument("--tournament", action="store_true")

    fuzz = sub.add_parser("fuzz", help="fuzz deterministic arena invariants")
    fuzz.add_argument("--seed", type=int, default=0)
    fuzz.add_argument("--cases", type=int, default=100)

    sparse = sub.add_parser("sparse-bench", help="compare full-scan and sparse scheduler work units")
    sparse.add_argument("--seed", type=int, default=0)
    sparse.add_argument("--entities", type=int, default=10_000)
    sparse.add_argument("--active", type=int, default=100)
    sparse.add_argument("--ticks", type=int, default=128)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "arena":
        left = AgentGenome("alpha", seek_resource=0.9, aggression=0.25, conservation=0.5, exploration=0.15)
        right = AgentGenome("beta", seek_resource=0.55, aggression=0.7, conservation=0.3, exploration=0.35)
        result = run_arena_t0(left, right, seed=args.seed, config=ArenaConfig(max_steps=args.steps))
        audit = audit_match(result)
        print(json.dumps({"match": result.to_dict(), "audit": audit.to_dict()}, sort_keys=True, ensure_ascii=False, indent=2))
        return 0 if audit.accepted else 2

    if args.command == "tournament":
        population = seed_population(args.population, seed=args.seed)
        report = run_round_robin(
            population,
            seeds=(args.seed, args.seed + 1, args.seed + 2),
            config=ArenaConfig(max_steps=args.steps),
            mirrored=True,
        )
        print(report.to_json(include_replays=False), end="")
        return 0

    if args.command == "evolve":
        config = EvolutionConfig(population_size=args.population, tournament_seeds=(args.seed, args.seed + 1))
        run = evolve(
            generations=args.generations,
            seed=args.seed,
            config=config,
            arena_config=ArenaConfig(max_steps=args.steps),
        )
        print(run.to_json(), end="")
        return 0

    if args.command == "quality-diversity":
        population = seed_population(args.population, seed=args.seed)
        experiment = run_quality_diversity(
            population,
            seeds=(args.seed, args.seed + 1),
            arena_config=ArenaConfig(max_steps=args.steps),
            archive_config=ArchiveConfig(bins=(args.bins, args.bins)),
        )
        print(experiment.to_json(include_matches=False), end="")
        return 0

    if args.command == "memory-demo":
        population = seed_population(args.population, seed=args.seed)
        arena_config = ArenaConfig(max_steps=args.steps)
        tournament = run_round_robin(
            population,
            seeds=(args.seed, args.seed + 1),
            config=arena_config,
            mirrored=True,
        )
        memory = EvolutionaryMemory()
        memory.admit_tournament(population, tournament, generation=0, top_k=args.top_k)
        candidate = seed_population(2, seed=args.seed + 10_000, prefix="candidate")[0]
        regression = evaluate_anti_forgetting(
            candidate,
            memory.hall_of_fame,
            seeds=(args.seed + 2, args.seed + 3),
            config=arena_config,
            threshold=args.threshold,
        )
        print(json.dumps({"memory": memory.to_dict(), "anti_forgetting": regression.to_dict()}, sort_keys=True, ensure_ascii=False, indent=2))
        return 0 if regression.passed else 4

    if args.command == "coevolve":
        population = seed_population(args.population, seed=args.seed)
        environments = seed_environments(args.environments, seed=args.seed + 1000)
        report = run_coevolution_cycle(
            population,
            environments,
            train_seeds=(args.seed, args.seed + 1),
            validation_seeds=(args.seed + 10_000, args.seed + 10_001),
            adversarial_limit=args.adversarial_limit,
        )
        next_environments = evolve_environments(
            environments,
            report,
            generation=0,
            seed=args.seed + 2000,
            target_size=args.next_environments,
        )
        print(json.dumps({"coevolution": report.to_dict(), "next_environments": [asdict(environment) for environment in next_environments]}, sort_keys=True, ensure_ascii=False, indent=2))
        return 0

    if args.command == "compile-spec":
        text = Path(args.path).read_text(encoding="utf-8")
        compiled = GameSpecCompiler().compile(text)
        payload = {"compiled": compiled.to_dict()}
        if compiled.accepted and args.tournament:
            tournament = compiled.run_tournament(seeds=(args.seed, args.seed + 1), mirrored=True)
            payload["tournament"] = tournament.to_dict(include_replays=False)
        print(json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2))
        return 0 if compiled.accepted else 5

    if args.command == "fuzz":
        report = fuzz_arena_t0(cases=args.cases, seed=args.seed)
        print(report.to_json(), end="")
        return 0 if report.accepted else 3

    if args.command == "sparse-bench":
        report = run_sparse_benchmark(entity_count=args.entities, active_entities=args.active, ticks=args.ticks, seed=args.seed)
        print(report.to_json(), end="")
        return 0

    print(json.dumps({"error": "unknown command", "args": vars(args)}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
