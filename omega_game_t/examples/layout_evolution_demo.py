from __future__ import annotations

import json
from pathlib import Path

from omega_game.engines.evolutionary_memory import EvolutionaryMemory
from omega_game.engines.game_spec import GameSpecCompiler
from omega_game.engines.layout_evolution import (
    LayoutEvolutionConfig,
    evaluate_layout_population,
    evaluate_map_generalization,
    evolve_layout_population,
    seed_layout_population,
)
from omega_game.engines.simulation import ArenaConfig


def main() -> int:
    spec_path = Path(__file__).with_name("game_spec_fixed_layout.json")
    compiled = GameSpecCompiler(layout_fairness_threshold=0.5).compile(spec_path.read_text(encoding="utf-8"))
    if not compiled.accepted or compiled.layout is None:
        raise SystemExit("fixed-layout example did not compile")

    memory = EvolutionaryMemory()
    layouts = seed_layout_population(
        compiled.layout,
        4,
        seed=700,
        mutation_steps=1,
        repair_attempts=128,
        fairness_threshold=0.5,
        memory=memory,
    )
    cfg = LayoutEvolutionConfig(
        population_size=4,
        elite_fraction=0.5,
        mutation_steps=1,
        repair_attempts=64,
        fairness_threshold=0.5,
        train_seeds=(1,),
        validation_seeds=(101,),
    )
    arena = ArenaConfig(max_steps=12)
    evaluation = evaluate_layout_population(compiled.agents, layouts, arena_template=arena, config=cfg)
    next_layouts = evolve_layout_population(
        layouts,
        evaluation,
        generation=0,
        seed=701,
        config=cfg,
        memory=memory,
    )

    held_out = seed_layout_population(
        compiled.layout,
        3,
        seed=900,
        mutation_steps=1,
        repair_attempts=128,
        fairness_threshold=0.5,
    )
    validation_layouts = tuple(
        layout for layout in held_out if layout.layout_hash not in {item.layout_hash for item in next_layouts}
    )
    if not validation_layouts:
        raise SystemExit("could not construct disjoint held-out maps")
    generalization = evaluate_map_generalization(
        compiled.agents,
        next_layouts,
        validation_layouts,
        seeds=(7,),
        arena_template=arena,
        fairness_threshold=0.5,
    )

    print(
        json.dumps(
            {
                "layout_evaluation": evaluation.to_dict(),
                "next_layout_hashes": [layout.layout_hash for layout in next_layouts],
                "map_generalization": generalization.to_dict(),
                "memory": memory.to_dict(),
            },
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
