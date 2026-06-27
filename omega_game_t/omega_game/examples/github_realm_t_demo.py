"""Run a minimal GitHubRealmEngine-T demo."""

from __future__ import annotations

import json

from omega_game.engines.github_realm import GitHubRealmEngine, demo_repo_world
from omega_game.kernel import GameEngineKernel


def main() -> None:
    repo_world = demo_repo_world()
    world = repo_world.to_world_state()
    result = GameEngineKernel().run_best_action(GitHubRealmEngine(), world)
    print(json.dumps({"repo_world": repo_world.to_dict(), "result": result.to_dict()}, indent=2))


if __name__ == "__main__":
    main()
