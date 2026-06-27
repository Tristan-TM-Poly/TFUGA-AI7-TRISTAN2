"""Run a minimal GameEngineOS-T demo."""

from __future__ import annotations

import json

from omega_game.engines.code_dojo import CodeDojoEngine, demo_world as code_world
from omega_game.engines.process_alchemy import ProcessAlchemyEngine, demo_world as process_world
from omega_game.engines.prototype_world import PrototypeWorldEngine, demo_world as prototype_world
from omega_game.kernel import GameEngineKernel


def main() -> None:
    kernel = GameEngineKernel()
    runs = [
        kernel.run_best_action(PrototypeWorldEngine(), prototype_world()),
        kernel.run_best_action(ProcessAlchemyEngine(), process_world()),
        kernel.run_best_action(CodeDojoEngine(), code_world()),
    ]
    print(json.dumps({"gameengineos": "GameEngineOS-T", "runs": [run.to_dict() for run in runs]}, indent=2))


if __name__ == "__main__":
    main()
