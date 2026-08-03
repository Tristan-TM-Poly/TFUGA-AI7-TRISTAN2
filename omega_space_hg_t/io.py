"""Mission-manifest loading and deterministic JSON emission."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import MissionConfig, OrbitState, SpacecraftConfig


def mission_from_dict(payload: dict[str, Any]) -> MissionConfig:
    orbit = payload["orbit"]
    spacecraft = payload["spacecraft"]
    config = MissionConfig(
        mission_id=str(payload["mission_id"]),
        objective=str(payload["objective"]),
        duration_s=float(payload["duration_s"]),
        step_s=float(payload["step_s"]),
        central_body_mu_m3_s2=float(payload["central_body_mu_m3_s2"]),
        central_body_radius_m=float(payload["central_body_radius_m"]),
        orbit=OrbitState(
            tuple(float(value) for value in orbit["position_m"]),
            tuple(float(value) for value in orbit["velocity_m_s"]),
            float(orbit.get("epoch_s", 0.0)),
        ),
        spacecraft=SpacecraftConfig(
            name=str(spacecraft["name"]),
            dry_mass_kg=float(spacecraft["dry_mass_kg"]),
            payload_mass_kg=float(spacecraft["payload_mass_kg"]),
            panel_area_m2=float(spacecraft["panel_area_m2"]),
            panel_efficiency=float(spacecraft["panel_efficiency"]),
            battery_capacity_wh=float(spacecraft["battery_capacity_wh"]),
            initial_battery_fraction=float(spacecraft["initial_battery_fraction"]),
            base_load_w=float(spacecraft["base_load_w"]),
            payload_load_w=float(spacecraft["payload_load_w"]),
            downlink_load_w=float(spacecraft["downlink_load_w"]),
            radiator_area_m2=float(spacecraft["radiator_area_m2"]),
            absorptivity=float(spacecraft.get("absorptivity", 0.35)),
            emissivity=float(spacecraft.get("emissivity", 0.82)),
            thermal_capacity_j_k=float(spacecraft.get("thermal_capacity_j_k", 25_000.0)),
            initial_temperature_k=float(spacecraft.get("initial_temperature_k", 293.15)),
            data_generation_mbps=float(spacecraft.get("data_generation_mbps", 2.0)),
            storage_capacity_gb=float(spacecraft.get("storage_capacity_gb", 128.0)),
            downlink_rate_mbps=float(spacecraft.get("downlink_rate_mbps", 40.0)),
        ),
        payload_duty_cycle=float(payload.get("payload_duty_cycle", 0.35)),
        downlink_duty_cycle=float(payload.get("downlink_duty_cycle", 0.12)),
        eclipse_fraction=float(payload.get("eclipse_fraction", 0.36)),
        solar_flux_w_m2=float(payload.get("solar_flux_w_m2", 1361.0)),
        albedo_flux_w_m2=float(payload.get("albedo_flux_w_m2", 110.0)),
        deep_space_temperature_k=float(payload.get("deep_space_temperature_k", 3.0)),
        theorem_claimed=bool(payload.get("theorem_claimed", False)),
        flight_qualified_claimed=bool(payload.get("flight_qualified_claimed", False)),
        scientific_validation_claimed=bool(payload.get("scientific_validation_claimed", False)),
        metadata=dict(payload.get("metadata", {})),
    )
    config.validate()
    return config


def load_mission(path: str | Path) -> MissionConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("mission manifest root must be an object")
    return mission_from_dict(payload)


def emit_json(payload: Any, output: str | Path | None = None) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is not None:
        Path(output).write_text(text, encoding="utf-8")
    return text
