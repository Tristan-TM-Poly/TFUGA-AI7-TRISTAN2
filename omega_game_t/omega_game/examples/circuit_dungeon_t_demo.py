"""Run a minimal CircuitDungeon-T demo.

Usage from this directory:

    python -m omega_game.examples.circuit_dungeon_t_demo
"""

from __future__ import annotations

from omega_game.engines import CircuitDungeonEngine


def main() -> None:
    dungeon = CircuitDungeonEngine.demo_dungeon()
    door = dungeon.doors["door_resonance_1"]
    target = door.resonance_frequency_hz

    success = dungeon.attempt_frequency("door_resonance_1", target)
    failure = dungeon.attempt_frequency("door_resonance_1", target * 1.5)
    gm_proposal = dungeon.tick_gm()

    print("Ω-GAME-T / CircuitDungeon-T demo")
    print("=" * 40)
    print("Target frequency Hz:", round(target, 6))
    print("Success opened:", success.opened)
    print("Failure opened:", failure.opened)
    print("M+ entries:", len(dungeon.gm.m_plus.entries))
    print("M- entries:", len(dungeon.gm.m_minus.entries))
    print("GM quest:", gm_proposal.quest["quest"])
    print("GM OAK accepted:", gm_proposal.oak_report.accepted if gm_proposal.oak_report else None)


if __name__ == "__main__":
    main()
