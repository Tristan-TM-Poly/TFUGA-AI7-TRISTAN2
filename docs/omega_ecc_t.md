# Ω-ECC-T — Error Correction Codes de Tristan

**Status:** exploratory executable canon layer. This module is a testable scaffold, not a claim of superiority over LDPC, Polar, Reed-Solomon, BCH, Turbo, Fountain/RaptorQ, surface codes, or qLDPC.

## Core thesis

A Tristan error-correction code does not merely add redundancy. It turns noise into a measurable syndrome, compresses the syndrome into fertile invariants, reconstructs under explicit constraints, and stores failed or uncertain corrections in M⁻.

```text
message -> encoder -> noisy channel -> syndrome-CVCD -> decoder -> OAK gate -> M⁺/M⁻
```

Canonical formula:

```text
Ω-ECC-T = OAK(EXP(CVCD(y), S_T, P(e | y, S_T, M⁻), C_T))
```

Where:

- `y` is the received corrupted object.
- `S_T` is the multi-scale syndrome tensor.
- `P(e | ...)` is the Bayes-Tristan error posterior.
- `C_T` is the code constraint system.
- `OAK` accepts, rejects, or asks for retransmission / more redundancy.

## Syndrome-CVCD

Classical syndrome:

```text
s = H yᵀ
```

Ω-ECC-T expands it into:

```text
S_T = (parity, erasure, burst, graph, scale, channel, Bayes, M⁻)
```

The goal is to make the smallest diagnostic object that is still sufficient for correction, rejection, or adaptation.

## HyperParityGraph-T

A parity-check matrix becomes a hypergraph:

```text
G_T = (V, E, H, W, Σ, M⁻)
```

- `V`: bits, symbols, packets, cells, DNA fragments, qubits, memories.
- `E`: parity / stabilizer / consistency hyperedges.
- `H`: binary or algebraic constraint operator.
- `W`: reliability weights.
- `Σ`: observed syndromes.
- `M⁻`: known failure modes and false-correction patterns.

LDPC is a special sparse case. Reed-Solomon is an algebraic reconstruction case. Fountain/RaptorQ is a generative erasure-recovery case. Quantum stabilizer codes are a syndrome-without-reading-the-state case.

## OAK rules

1. No infinite correction.
2. Always state the channel model.
3. Always compare against baselines.
4. Distinguish detection, correction, erasure recovery, integrity, and security.
5. ECC is not cryptography.
6. A correction with low confidence is an OAK rejection, not a success.
7. Superiority requires measured BER/BLER/FER, rate, distance, latency, complexity, energy, and false-accept rate.

## MVP implemented in this PR

- Hamming(7,4) encoder / decoder.
- Binary symmetric, burst-flip, and erasure-like channels.
- `ChannelReport.syndrome_hint()` as the first Syndrome-CVCD diagnostic.
- `HyperParityGraph` with exhaustive nearest-codeword decoding for small binary graphs.
- OAK gate for accepting/rejecting Hamming(7,4) corrections.
- M⁻ JSONL event hook.
- Deterministic benchmark: `bench_hamming74_bsc`.

## Next expansions

1. LDPC sparse graph + belief propagation / min-sum.
2. Reed-Solomon over GF(2^m) or a dependency-backed implementation.
3. Polar code scaffold with successive cancellation.
4. Fountain/erasure codes for packet loss.
5. FFWT-noise profiler for burst/fractal/correlated errors.
6. BayesDecoder_T with soft information.
7. qLDPC / stabilizer-code exploratory notebook.
8. OAKBench matrix: BSC, BEC, AWGN, burst, flash-like, DNA-like indel/loss, quantum depolarizing.

## Memory-negative registry

Initial M⁻ constraints:

- A named Tristan code is not better until it beats a baseline under a named channel.
- Hamming(7,4) corrects one bit; two-bit errors may be miscorrected.
- Redundancy improves reliability but costs rate, energy, memory, and latency.
- Correction is not authentication.
- Fractal/mycelial topology must become a measurable parity structure, not only a metaphor.
