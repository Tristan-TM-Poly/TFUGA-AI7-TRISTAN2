# Canon Extreme Issue Map

This map links the first OAK issues to the new executable and documentation layers.

## Active OAK issues

| Issue | Purpose | Target level | Implemented seed in PR #17 |
|---|---|---|---|
| #18 | Define Omega-FFWT coefficient tensor and minimal API | OAK-2 | `sage_tristan/omega_ffwt.py`, `docs/omega-ffwt-mvp-api.md` |
| #19 | Build synthetic signal generator for FFWT benchmarks | OAK-3 | `generate_signal`, `run_minimal_benchmark`, `examples/omega_ffwt_demo.py` |
| #20 | Compare Omega-FFWT candidate against FFT/DWT baselines | OAK-5 future | naive DFT concentration baseline added; stronger baselines still needed |

## Next issues to create

1. Add coefficient thresholding and lossy reconstruction benchmark.
2. Export benchmark reports to `reports/` automatically.
3. Add phase metrics with mandatory real projection.
4. Add quaternion-style commutator defect metrics.
5. Add octonion-style associator defect metrics.
6. Add explicit M_MINUS writer when a baseline wins.
7. Add Genesis Atlas node for each new theory card.

## Current promotion boundary

The MVP can support an `OAK-3 candidate` status because it is executable, deterministic, and tested on synthetic signals.

It should **not** be promoted to OAK-5/OAK-6 until stronger baselines, saved result tables, and failure cases exist.
