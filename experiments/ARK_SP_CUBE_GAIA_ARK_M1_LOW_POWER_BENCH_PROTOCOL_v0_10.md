# ARK-SP-CUBE-GAIA v0.10 — Ark-M1 Low-Power Bench Protocol

## Status OAK

```yaml
status: C_experimental_protocol
hardware_validation: false
energy_device_certification: false
safety_level: low_power_only
human_review_required: true
```

## Purpose

Turn Ark-M1 from a conceptual energy/thermal core into a low-power measurable bench.

This protocol is intentionally small: the goal is not to demonstrate a reactor, a product, or high-power device. The goal is to measure heat, loss, and cooling response safely.

## Core hypothesis

```text
H_ARK_001: A low-power Ark-M1 bench can log stable voltage, current, power, and temperature traces suitable for testing SP-CUBE thermal coupling.
```

## Minimal bench

- safe low-voltage power source
- resistive heat load below 10 W
- temperature sensor near heat load
- temperature sensor near SP-CUBE or cooling surface
- voltage/current measurement
- timestamped logger
- manual cutoff or safe disconnect

## Primary equations

```text
P_heat = V * I
```

```text
G_cool = (T_without_SP - T_with_SP) / P_heat
```

Unit:

```text
degC / W
```

## Measurement phases

1. Baseline with no SP-CUBE surface.
2. Reference surface attached.
3. SP-CUBE passive candidate attached.
4. Cooldown period.
5. Repeat on separate run.

## Logging schema

```csv
timestamp,run_id,mode,voltage_v,current_a,power_w,heat_load_temp_c,cool_surface_temp_c,air_temp_c,operator_note
```

## OAK safety gates

Stop the run if:

- unexpected heating occurs
- sensor reading is unstable or disconnected
- current exceeds expected range
- any component becomes unsafe to touch
- battery, wiring, or connector risk appears

## Allowed claims after first dataset

- low-power bench trace collected
- temperature response measured
- SP-CUBE coupling candidate tested

## Forbidden claims after first dataset

- energy generation
- certified device performance
- product readiness
- climate-credit value
- safety certification

## Next route

If measured traces exist, route:

```text
Ark-M1 bench -> Infra-QC asset -> OAK proof ledger -> SP-CUBE comparison experiment
```
