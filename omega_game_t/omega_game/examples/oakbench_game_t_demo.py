"""Run OAKBench-GAME-T across the current Ω-GAME-T engines.

Usage from this directory:

    python -m omega_game.examples.oakbench_game_t_demo
"""

from __future__ import annotations

import json

from omega_game.bench import default_engine_benchmarks


def main() -> None:
    runner = default_engine_benchmarks()
    report = runner.report()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
