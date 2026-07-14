# ARK-SP-CUBE-GAIA v0.10 — SP-CUBE Passive Delta-T Protocol

## Status OAK

```yaml
status: C_experimental_protocol
physical_validation: false
certified_performance: false
safety_level: low_power_passive_only
human_review_required: true
```

## Purpose

Turn the SP-CUBE concept from a spectral/radiative hypothesis into a first measurable passive cooling experiment.

This protocol does not prove a product, a material breakthrough, or certified climate impact. It only defines the first low-risk measurement gate.

## Core hypothesis

```text
H_SP_001: A SP-CUBE-inspired surface can produce a lower measured surface temperature than at least one controlled baseline under comparable conditions.
```

## Falsification condition

```text
If T_sp_cube(t) >= T_baseline(t) across repeated controlled trials, the cooling claim remains unmeasured or is downgraded/refuted for that configuration.
```

## Minimal samples

- S0: polished or reflective aluminum reference
- S1: white cool-surface reference
- S2: black matte reference
- S3: textured or cavity-inspired IR surface
- S4: SP-CUBE mycelial/selective candidate

## Minimal sensors

- surface temperature for every sample
- ambient air temperature
- timestamp
- weather/sky note
- solar condition note
- optional humidity
- optional irradiance proxy

## Primary metric

```text
DeltaT_i(t) = T_reference(t) - T_sample_i(t)
```

Suggested references:

- white reference for practical cool-surface comparison
- black matte reference for high-absorption comparison
- aluminum reference for reflective comparison

## Score

```text
SP_deltaT_score = mean(T_best_reference - T_sp_cube)
```

A positive score is only a measured cooling candidate, not certification.

## Logging schema

```csv
timestamp,sample_id,surface_temp_c,air_temp_c,sky_note,solar_note,humidity_pct,irradiance_proxy,operator_note
```

## OAK gates

- IDEA: no sample exists
- FORMALIZED: protocol exists
- PROTOTYPED: samples assembled
- MEASURED: timestamped dataset exists
- REPRODUCED: repeated on separate days or by separate setup
- EXTERNAL_REVIEW: reviewed by a qualified third party
- CERTIFIED: only through an external standard or accepted methodology

## Non-claims

This protocol does not claim:

- net cooling in all weather
- certified radiative cooling performance
- climate-credit value
- energy creation
- product readiness

## Next route

If a first dataset exists, route the claim to:

```text
SP-CUBE -> Infra-QC asset -> OAK issue draft -> public-safe proof ledger
```
