# Passive LC/RLC Resonance Protocol

Status: OAK-3 simulation-first protocol seed.  
Related issue: #25.

This document keeps the LC/RLC branch in a safe and testable form: passive circuits, explicit assumptions, reference topology and measured or simulated resonance curves.

---

## 1. Goal

Compare a simple regular LC/RLC network with a fractal or multi-scale variant under the same component constraints.

The first target is not a broad physical claim. The first target is a reproducible frequency response comparison.

---

## 2. Required comparison

Every experiment must include:

- baseline network;
- proposed multi-scale network;
- same component ranges;
- frequency sweep;
- impedance or transfer response;
- loss model;
- resonance peak table;
- residue notes.

---

## 3. Metrics

| Metric | Meaning |
|---|---|
| resonance_frequency | peak or local maximum frequency |
| q_factor | sharpness of resonance |
| bandwidth | frequency width around resonance |
| peak_gain | transfer response peak |
| loss_estimate | dissipative component estimate |
| sensitivity | change under component perturbation |
| baseline_delta | difference from regular network |

---

## 4. Minimal simulation files

Suggested paths:

```text
experiments/lc_rlc_passive/baseline_lc_ladder.net
experiments/lc_rlc_passive/fractal_lc_ladder.net
experiments/lc_rlc_passive/report_template.md
```

---

## 5. Review status gates

```text
CONCEPT -> SIMULATION_READY -> SIMULATED -> MEASUREMENT_READY -> MEASURED
```

Rules:

- simulated curves stay simulated;
- measured curves require instrument notes and raw data;
- broad physical interpretation requires separate review;
- failed comparisons are useful and should be preserved.

---

## 6. First minimal test

1. Choose a baseline RLC ladder.
2. Choose a multi-scale ladder with comparable total component count.
3. Run AC sweep.
4. Extract resonance peaks and bandwidth.
5. Compare against baseline.
6. Write OAKReport with residue and next test.
