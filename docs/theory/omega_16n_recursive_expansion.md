# Omega 16^n Recursive Expansion Canon

**Status:** `FORMALIZED / EXECUTABLE_SYMBOLIC / OAK_GUARDED`

This document stabilizes the `x16^n` directive as a recursive generator for the Tristan ecosystem.

It does not mean blindly materializing every possible branch at all depths. It means building a symbolic 16-branch expansion operator that can enumerate small depths, summarize large depths, score cells, and keep generated claims under OAK status discipline.

```text
16^n is a search geometry, not a proof.
16^n is a generator, not automatic truth.
16^n must be compressed, scored, sampled and OAK-gated.
```

## 1. Core definition

Let `B16 = {0, 1, ..., F}` be sixteen branches/operators/chambers. A recursive path of depth `n` is a hex word of length `n`.

The raw number of paths is:

```text
N(n) = 16^n
```

OAK rule:

```text
raw generated path != certified claim
```

## 2. Symbolic expansion operator

Define an operator `Omega16(x)` that returns sixteen transformed candidates from a seed `x`.

Repeated expansion gives:

```text
Omega16^n(x)
```

The uncompressed expansion has `16^n` leaves. The compressed representation stores only:

```text
(seed, branch_set, depth, score_rule, oak_rule, sampling_rule)
```

This prevents combinatorial explosion.

## 3. Base-16 path encoding

A path is a word like:

```text
0A4F
```

For fixed depth `n`, a path corresponds to an integer:

```text
q(path) = sum(digit_k * 16^(n-k))
```

This is reversible for fixed-length hex words.

## 4. Sixteen canonical branches

| Hex | Branch | Function |
|---:|---|---|
| 0 | Trace | extract trace |
| 1 | Transform | apply transformation |
| 2 | Maintain | detect persistence |
| 3 | Hypergraphize | build HGFM relation |
| 4 | Compress | LOG/CVCD compression |
| 5 | Expand | EXP/decompression |
| 6 | Factorize | tensor/core decomposition |
| 7 | Invariantize | extract invariant |
| 8 | Residualize | compute residue/error |
| 9 | Compose | compose morphisms/claims |
| A | Generalize | extend scope carefully |
| B | Dualize | build dual/projection |
| C | Challenge | search stress case |
| D | CertifyLocal | assign OAK status |
| E | Memorize | update positive/negative memory |
| F | Reinject | generate next cycle |

## 5. Fertility scoring

A path receives a score:

```text
score = novelty * plausibility * utility * compressibility
        / (cost + risk + residue + epsilon)
```

Then CVCD keeps a frontier instead of all leaves:

```text
frontier = TopK(paths, score)
```

## 6. Negative memory penalty

Generated paths close to known failed patterns are demoted:

```text
score_prime(path) = score(path) - lambda * max_similarity(path, M_MINUS)
```

## 7. Symbolic vs materialized expansion

Small depths may be enumerated:

```text
n <= 3 gives at most 4096 paths
```

Large depths must be symbolic or sampled:

```text
n > 3 => symbolic + sampling + TopK + OAK
```

## 8. Theorem: path count

For any `n >= 0`, a complete 16-branch expansion has `16^n` paths.

Proof: each of the `n` levels has 16 independent choices. By the multiplication rule, the number of paths is `16 * ... * 16 = 16^n`.

## 9. Theorem: fixed-length hex encoding

For fixed depth `n`, the mapping from a hex word of length `n` to an integer in `[0, 16^n - 1]` is bijective.

Proof: this is uniqueness of fixed-length base-16 representation.

## 10. OAK status matrix

| Claim | Status | Reason |
|---|---|---|
| There are 16^n raw paths | `PROVED_LOCAL` | multiplication rule |
| Each path has reversible hex encoding | `PROVED_LOCAL` | base-16 representation |
| All paths are useful | `REJECTED_OVERCLAIM` | requires scoring and evidence |
| All paths are true | `M_MINUS_GUARDRAIL` | generation is not proof |
| Symbolic expansion avoids full materialization | `EXECUTABLE_SYMBOLIC` | implemented by generator |

## 11. Canon rule

```text
x16^n = recursive 16-branch generation + CVCD compression + OAK filtering
```

The useful object is not the raw explosion. The useful object is the compressed, scored, testable frontier.
