"""Run a minimal ScienceSandbox-T demo.

Usage from this directory:

    python -m omega_game.examples.science_sandbox_t_demo
"""

from __future__ import annotations

from omega_game.engines import (
    MicrogridParams,
    MicrogridState,
    RLCParams,
    RLCState,
    ScienceSandboxEngine,
)


def main() -> None:
    sandbox = ScienceSandboxEngine()

    rlc_result = sandbox.step_rlc(
        state=RLCState(q_coulomb=0.0, i_ampere=0.0),
        params=RLCParams(
            resistance_ohm=10.0,
            inductance_henry=0.1,
            capacitance_farad=0.001,
            source_voltage_volt=5.0,
        ),
        dt_second=0.001,
    )

    microgrid_result = sandbox.step_microgrid(
        state=MicrogridState(battery_energy_wh=250.0),
        params=MicrogridParams(
            battery_capacity_wh=1000.0,
            roundtrip_efficiency=0.9,
            max_charge_power_w=400.0,
            max_discharge_power_w=400.0,
        ),
        solar_power_w=300.0,
        load_power_w=500.0,
        dt_hour=0.25,
    )

    gm_proposal = sandbox.tick_gm()

    print("Ω-GAME-T / ScienceSandbox-T demo")
    print("=" * 40)
    print("RLC current A:", round(rlc_result.state.i_ampere, 6))
    print("RLC energy residue J:", round(rlc_result.energy_residue_joule, 9))
    print("Microgrid battery Wh:", round(microgrid_result.state.battery_energy_wh, 3))
    print("Microgrid unmet load Wh:", round(microgrid_result.unmet_load_wh, 3))
    print("M+ entries:", len(sandbox.gm.m_plus.entries))
    print("M- entries:", len(sandbox.gm.m_minus.entries))
    print("GM quest:", gm_proposal.quest["quest"])
    print("GM OAK accepted:", gm_proposal.oak_report.accepted if gm_proposal.oak_report else None)


if __name__ == "__main__":
    main()
