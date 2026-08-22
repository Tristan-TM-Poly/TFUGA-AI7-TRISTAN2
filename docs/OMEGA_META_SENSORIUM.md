# Ω Meta Sensorium Morphogenesis T∞ — v1

## Purpose

Turn satellite/telescope/detector design into a proof-carrying science-to-observation compilation problem. The v1 implementation deliberately starts with existing capabilities and minimum-sufficient observation planning before any hardware-generation layer.

## Mother loop

`WORLD -> RESIDUAL -> QUESTION -> HYPOTHESES -> OBSERVABLES -> EXISTING CAPABILITIES -> MINIMAL WITNESS -> OBSERVE -> CALIBRATE -> RECEIPT -> VERIFY -> UPDATE WORLD MODEL`

Orthogonal lifecycle:

`GENERATE -> CONTRAST -> SIMULATE -> ABLATE -> VERIFY -> DISTILL M+/M-/M? -> PRUNE -> REGENERATE`

## Core distinctions

- Instrument != evidence.
- Simulation != observation.
- Generated detector genome != physically realizable detector.
- Better score != scientific truth.
- Agreement != independent verification.
- More sensors != more science.
- More data != more information.
- Existing capability should be searched before new hardware is proposed.

## v1 executable capabilities

1. `ScienceToSensorCompiler`: finds the least-cost existing sensor set that covers required observables.
2. `MinimalWitnessCompiler`: selects the cheapest candidate that crosses explicit discrimination and calibration thresholds and beats a NO_ACTION baseline.
3. `ActiveObservationEngine`: ranks follow-up observations by calibrated information value per cost/risk/complexity/debt.
4. `ObservationCourt`: requires independent verifier role, raw-data hashes, processing-pipeline identity, provenance, bounded uncertainty and calibration versions.
5. `MetaSensorium`: delegates meta-stop decisions to the existing `omega_morphogenesis.MorphogenesisKernel` rather than creating a duplicate meta-kernel.

## Future residuals, not yet claimed capabilities

- multi-messenger event compiler;
- detector-material/readout co-design with physical simulators;
- orbit/formation-flying optimization;
- correlated failure portfolio optimization;
- synthetic-aperture and distributed-interferometry solvers;
- active observation over real telescope APIs;
- calibration drift digital twins;
- observatory federation capability contracts;
- counterfactual universe and AntiDiscovery generators;
- causal architecture attribution;
- regenerative mission digital twins.

These remain roadmap items until implemented and benchmarked.

## OAK gates

Every scientific use should preserve:

`ClaimScope <= EvidenceScope`

`Generator != Judge`

`Generated != Verified`

`Simulation != Observation`

`Capability != Authority`

`NO_ACTION is valid`

No score compensates for missing calibration, missing provenance, unsafe authority, invalid physics or lack of independent verification.

## Minimum Sufficient Observatory

For a question Q, seek the least-cost capability set that covers the explicitly required observables. The v1 compiler solves a small exact subset search over declared capabilities. It is a software reference model, not a mission-design optimizer.

## Observation value

The reference candidate value is:

`expected_information_gain * discrimination_power * calibration_confidence * evidence_independence / (1 + resource_cost + risk + complexity + epistemic_debt)`

This is a tunable heuristic. It is not a universal law and should be calibrated against real mission objectives.

## Regeneration

`BOOK0_OMEGA_META_SENSORIUM_V1` records the minimal source set, invariants, falsifiers and rebuild command. If ablation proves a smaller set preserves the frozen behavior, this BOOK0 should shrink.
