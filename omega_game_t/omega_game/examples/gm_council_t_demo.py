"""Run a minimal GM-Council-T demo.

Usage from this directory:

    python -m omega_game.examples.gm_council_t_demo
"""

from __future__ import annotations

import json

from omega_game import default_gm_council
from omega_game.engines import TextWorldEngine


def main() -> None:
    engine = TextWorldEngine.demo_world()
    council = default_gm_council()
    decision = council.deliberate(engine.world)

    print("Ω-GAME-T++ / GM-Council-T demo")
    print("=" * 40)
    print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
