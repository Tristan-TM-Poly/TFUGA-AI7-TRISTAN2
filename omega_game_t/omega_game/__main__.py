from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .engines import (
    AgentGenome,
    ArenaConfig,
    EvolutionConfig,
    audit_match,
    evolve,
    fuzz_arena_t0,
    run_arena_t0,
    run_round_robin,
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

    fuzz = sub.add_parser("fuzz", help="fuzz deterministic arena invariants")
    fuzz.add_argument("--seed", type=int, default=0)
    fuzz.add_argument("--cases", type=int, default=100)
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

    if args.command == "fuzz":
        report = fuzz_arena_t0(cases=args.cases, seed=args.seed)
        print(report.to_json(), end="")
        return 0 if report.accepted else 3

    print(json.dumps({"error": "unknown command", "args": asdict(args) if hasattr(args, "__dataclass_fields__") else vars(args)}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
