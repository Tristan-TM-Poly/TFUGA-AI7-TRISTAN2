"""Run a minimal EnergyCivilization-T demo.

Usage from this directory:

    python -m omega_game.examples.energy_civilization_t_demo
"""

from __future__ import annotations

from omega_game.engines import EnergyCivilizationEngine, EnergyTurnInput


def main() -> None:
    engine = EnergyCivilizationEngine.demo_civilization()

    sunny_turn = engine.play_turn(
        "colony_solar_1",
        EnergyTurnInput(solar_power_w=800.0, load_power_w=300.0, dt_hour=0.5),
    )
    stressed_turn = engine.play_turn(
        "colony_solar_1",
        EnergyTurnInput(solar_power_w=100.0, load_power_w=900.0, dt_hour=0.5),
    )
    gm_proposal = engine.tick_gm()

    print("Ω-GAME-T / EnergyCivilization-T demo")
    print("=" * 40)
    print("Sunny score:", round(sunny_turn.energy_score, 4))
    print("Sunny service ratio:", round(sunny_turn.service_ratio, 4))
    print("Stressed score:", round(stressed_turn.energy_score, 4))
    print("Stressed unmet Wh:", round(stressed_turn.unmet_load_wh, 4))
    print("Battery Wh:", round(stressed_turn.battery_energy_wh, 4))
    print("M+ entries:", len(engine.gm.m_plus.entries))
    print("M- entries:", len(engine.gm.m_minus.entries))
    print("GM quest:", gm_proposal.quest["quest"])
    print("GM OAK accepted:", gm_proposal.oak_report.accepted if gm_proposal.oak_report else None)


if __name__ == "__main__":
    main()
