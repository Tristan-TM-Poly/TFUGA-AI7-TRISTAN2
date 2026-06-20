# Omega-FFWT-HAC-CVCD Roadmap

**Status:** priority branch, OAK-1/OAK-2 until executable benchmarks exist.

This roadmap turns Omega-FFWT-HAC-CVCD into a concrete scientific prototype path.

## Goal

Build a reproducible pipeline for multiscale signal analysis with hyperalgebraic coherence and strict OAK validation.

```text
signal
→ FFWT or wavelet-like multiscale transform
→ HAC metrics
→ CVCD invariant extraction
→ baseline comparison
→ OAK verdict
→ canon or M_MINUS
```

## Minimum viable prototype

### MVP-0 — Definitions

Deliverables:

- define FFWT input/output;
- define coefficient tensor shape;
- define HAC metrics;
- define CVCD outputs;
- define baselines and metrics.

Promotion target: `OAK-2`.

### MVP-1 — Synthetic signals

Datasets:

- sine wave;
- chirp;
- step function;
- white noise;
- pink-like noise;
- synthetic fractal/noisy signal.

Metrics:

- reconstruction error;
- energy concentration;
- noise stability;
- phase/coherence consistency;
- runtime;
- baseline delta.

Promotion target: `OAK-3`.

### MVP-2 — Real/complex HAC

Implement:

- real covariance/coherence;
- complex phase coherence;
- real projection always retained;
- baseline comparison with FFT/DWT/PCA/SVD where applicable.

Promotion target: `OAK-4/OAK-5`.

### MVP-3 — Quaternion/octonion defect metrics

Implement:

- commutator defect for quaternion-like products;
- associator defect for octonion-like products;
- interpret defects as measured invariants, not proof of meaning.

Promotion target: `OAK-5` only if benchmarked.

### MVP-4 — Sedenion safety layer

Implement:

- real projection;
- zero-divisor risk flag;
- instability detector;
- strict M_MINUS logging.

Promotion target: `OAK-4` initially, higher only after strong evidence.

## Baseline matrix

| Baseline | Purpose |
|---|---|
| FFT | frequency reference |
| STFT | time-frequency reference |
| DWT | wavelet reference |
| CWT | continuous scale reference |
| PCA | linear compression reference |
| SVD | matrix factorization reference |
| Random forest/SVM | simple classification reference |
| small autoencoder | neural compression reference |

## OAK success criteria

A result can be promoted only if:

1. the script is reproducible;
2. the dataset or generator is included;
3. the baseline is explicit;
4. the metric is explicit;
5. failures are logged;
6. M_MINUS is updated when needed;
7. claims stay local to the tested domain.

## First GitHub issues to create

1. `[OAK] Define Omega-FFWT coefficient tensor and minimal API`
2. `[OAK] Build synthetic signal generator for FFWT benchmarks`
3. `[OAK] Compare simple FFWT-like transform against FFT/DWT on reconstruction and stability`
4. `[OAK] Add complex HAC phase coherence metrics`
5. `[OAK] Add M_MINUS entry for failed or unstable algebraic claims`
6. `[OAK] Write first benchmark report`

## Canon boundary

Safe claim now:

```text
Omega-FFWT-HAC-CVCD is a candidate framework for multiscale invariant extraction using hyperalgebraic coherence metrics.
```

Unsafe claim now:

```text
Omega-FFWT-HAC-CVCD is universally better than existing transforms.
```

Promotion requires measurements.
