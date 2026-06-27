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

## GF(2) algebra layer

`ecc_tristan.gf2` provides the algebraic base that the first Ω-ECC-T PR was missing:

- binary vector/matrix validation;
- dot product, matrix-vector, vector-matrix multiplication over GF(2);
- transpose;
- RREF over GF(2);
- rank;
- nullspace basis;
- Hamming weight and Hamming distance;
- exhaustive binary vector generation for small OAK baselines.

This turns parity-check intuition into executable algebra.

## LinearBlockCode phase

`ecc_tristan.linear_block_code.LinearBlockCode` adds true code construction:

```text
H -> nullspace(H) = generator matrix G
message m -> codeword c = mG
received y -> exhaustive nearest-codeword ML decode
```

Implemented scope:

- construction from a generator matrix;
- construction from parity checks via GF(2) nullspace;
- encode;
- syndrome;
- codeword enumeration;
- minimum distance for small codes;
- rate calculation;
- exhaustive maximum-likelihood nearest-codeword decoder;
- explicit tie status: `nearest_tie_oak_uncertain`.

OAK-safe limit: exhaustive decoding is only for small research codes and correctness baselines. It must not be treated as a scalable decoder.

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

## SparseLDPC-T phase

`ecc_tristan.ldpc.SparseLDPC` adds the first sparse parity-check scaffold:

```text
H sparse -> syndrome -> unsatisfied checks -> iterative bit flips -> OAK residual status
```

Implemented scope:

- sparse binary parity-check matrix validation;
- bit-to-check / check-to-bit adjacency maps;
- syndrome calculation;
- hard-decision Gallager-style bit-flip decoder;
- explicit stalled / max-iteration failure statuses;
- tiny `toy_6_3` code for deterministic tests.

OAK-safe limit: this is not yet optimized LDPC belief propagation, sum-product, min-sum, normalized min-sum, offset min-sum, layered decoding, or hardware-aware decoding. It is a transparent scaffold for those next layers.

## Soft channel phase

`ecc_tristan.soft_channels` adds BPSK + AWGN log-likelihood ratios:

```text
bit 0 -> +1, bit 1 -> -1
LLR = 2y / σ²
```

This prepares BayesDecoder_T and min-sum/soft LDPC decoding. The first `reliability_cvcd()` extracts weak positions from LLR magnitudes.

## Soft-decision min-sum phase

`ecc_tristan.minsum.min_sum_decode()` implements the first soft-decision LDPC message-passing decoder:

```text
channel LLR -> variable-to-check messages -> check-to-variable min-sum -> posterior LLR -> hard decision -> syndrome/OAK
```

Supported controls:

- `max_iterations` for OAK-bounded inference;
- `normalize` for normalized min-sum;
- `offset` for offset min-sum;
- explicit `converged`, `max_iterations_residual`, and reliability outputs;
- `weak_positions` from posterior LLR magnitudes.

OAK-safe limit: this is a clean research decoder, not a production LDPC engine. Production-grade LDPC still needs real code construction, generator matrices, interleavers, puncturing/shortening, layered schedules, numerical stability, SIMD/GPU/hardware concerns, and comparison against mature libraries.

## Interleaver anti-burst phase

`ecc_tristan.interleaver` adds block interleaving:

```text
encoded blocks -> interleave -> burst channel -> deinterleave -> decode blocks
```

The interleaver does not create information. It spreads a contiguous burst across multiple codewords so a small component code, such as Hamming(7,4), may correct the distributed damage. OAKBench now compares burst performance with and without interleaving.

## OAKBench matrix

`ecc_tristan.oakbench_matrix.default_oakbench_matrix()` now emits a small benchmark table over:

- Hamming(7,4) on BSC at multiple flip probabilities;
- toy LDPC hard-decision bit-flip on BSC;
- toy LDPC soft-decision min-sum on BPSK/AWGN;
- toy linear code exhaustive ML decoding on BSC;
- Hamming(7,4) burst channel with and without block interleaving.

This is the seed of the full OAKBench matrix:

```text
BSC, BEC, AWGN, burst, packet-loss, flash-like, DNA-like indel/loss, quantum depolarizing
```

## OAK rules

1. No infinite correction.
2. Always state the channel model.
3. Always compare against baselines.
4. Distinguish detection, correction, erasure recovery, integrity, and security.
5. ECC is not cryptography.
6. A correction with low confidence is an OAK rejection, not a success.
7. Superiority requires measured BER/BLER/FER, rate, distance, latency, complexity, energy, and false-accept rate.

## Implemented executable layers

- Hamming(7,4) encoder / decoder.
- Binary symmetric, burst-flip, erasure-like, and BPSK/AWGN channels.
- `ChannelReport.syndrome_hint()` as the first Syndrome-CVCD diagnostic.
- GF(2) linear algebra.
- `LinearBlockCode` with construction from parity checks and exhaustive ML decode.
- `HyperParityGraph` with exhaustive nearest-codeword decoding for small binary graphs.
- OAK gate for accepting/rejecting Hamming(7,4) corrections.
- M⁻ JSONL event hook.
- Deterministic benchmark: `bench_hamming74_bsc`.
- `SparseLDPC` hard-decision decoder scaffold.
- Soft-decision min-sum decoder over LLR messages.
- Block interleaver / deinterleaver.
- `default_oakbench_matrix()` for deterministic comparison rows.

## Next expansions

1. Larger LDPC code construction with generator matrix and sparse ensembles.
2. Reed-Solomon over GF(2^m) or a dependency-backed implementation.
3. Polar code scaffold with successive cancellation.
4. Fountain/erasure codes for packet loss.
5. FFWT-noise profiler for burst/fractal/correlated errors.
6. BayesDecoder_T with soft information and M⁻ priors.
7. qLDPC / stabilizer-code exploratory notebook.
8. OAKBench matrix: BSC, BEC, AWGN, burst, flash-like, DNA-like indel/loss, quantum depolarizing.

## Memory-negative registry

Initial M⁻ constraints:

- A named Tristan code is not better until it beats a baseline under a named channel.
- Hamming(7,4) corrects one bit; two-bit errors may be miscorrected.
- Redundancy improves reliability but costs rate, energy, memory, and latency.
- Correction is not authentication.
- Fractal/mycelial topology must become a measurable parity structure, not only a metaphor.
- The toy LDPC is a scaffold, not a production code or performance claim.
- Hard-decision bit flipping can stall or converge to a wrong codeword; OAK must track residual and false-accept rate.
- Soft-decision min-sum is not automatically better; it must beat hard-decision and external LDPC baselines under identical channel assumptions.
- Exhaustive ML decoding is a correctness oracle for small codes, not a scalable solution.
- Interleaving can mitigate bursts, but it adds latency and does not increase Shannon capacity.
