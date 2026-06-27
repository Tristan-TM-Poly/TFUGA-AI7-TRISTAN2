"""Run a minimal Quest-CVCD demo.

Usage from this directory:

    python -m omega_game.examples.quest_cvcd_demo
"""

from __future__ import annotations

from omega_game.engines import TextWorldEngine


def main() -> None:
    engine = TextWorldEngine.demo_world()
    proposal = engine.tick()

    print("Ω-GAME-T / Quest-CVCD demo")
    print("=" * 40)
    print(engine.render_last_memory())
    print("\nOAK accepted:", proposal.oak_report.accepted if proposal.oak_report else None)
    print("OAK reasons:", proposal.oak_report.reasons if proposal.oak_report else [])


if __name__ == "__main__":
    main()
