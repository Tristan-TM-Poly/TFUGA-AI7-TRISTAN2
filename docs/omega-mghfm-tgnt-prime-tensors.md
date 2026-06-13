# Omega MGHFM TGNT Prime Tensor Canon

Status: exploratory formalization scaffold with executable prototype.

This document records a compact formal layer for prime tensors, gap tensors, HGFM relations, LOG/EXP compression-expansion, CVCD controlled decompression, JKD minimal action, YY3 triple flow, and OAK verification.

## Executable layer

The definitions in this file are now backed by a stdlib-only prototype:

- `sage_tristan/prime_tensors.py`
- `tests/test_prime_tensors.py`
- `examples/prime_tensor_demo.py`
- `reports/prime_tensor_oak_report.md`

Local validation before push:

```bash
PYTHONPATH=/tmp python -m unittest test_prime_tensors.py
PYTHONPATH=/tmp python -m sage_tristan.prime_tensors --count 6 --max-jump 2 > /tmp/packet.json
python -m json.tool /tmp/packet.json
```

Result: 5 tests passed and the JSON OAK packet was valid.

## Prime coordinate tensor

Let p_1 = 2, p_2 = 3, p_3 = 5, ... and P_0 = 1, P_j = product_{m=1..j} p_m.

For 1 <= j < i, define:

```math
T_{ij} = floor(p_i / P_{j-1}) mod p_j.
```

This gives the mixed-radix primorial coordinates of p_i in the basis of earlier primes.

With overflow C_i:

```math
p_i = C_i P_{i-1} + sum_{j=1}^{i-1} T_{ij} P_{j-1}.
```

## Residue tensor

```math
R_{ij} = p_i mod p_j, j < i.
```

Since p_i and p_j are distinct primes, R_{ij} is never zero.

## Gap tensor

For n >= 1:

```math
Delta_i^{(n)} = p_{i+n} - p_i.
```

Define:

```math
G_{i,n,j} = floor((p_{i+n}-p_i)/P_{j-1}) mod p_j.
```

and:

```math
D_{i,n,j} = (p_{i+n}-p_i) mod p_j.
```

Then:

```math
D_{i,n,j} = (R_{i+n,j} - R_{i,j}) mod p_j.
```

## HGFM node

Each prime becomes a node:

```text
v_i = (p_i, T_i, R_i, G_i, D_i, OAK_i, F_i)
```

where OAK_i is the verification status and F_i is the fertility score.

## Hyperedges

Create hyperedges for shared structures:

- same gap pattern,
- same residue signature,
- same primorial coordinate signature,
- same transformed gap tensor,
- same OAK-tested motif.

## LOG / EXP

LOG compresses raw structures into signatures:

```text
raw data -> motifs -> invariants -> rules -> meta-rules -> fertile signature
```

EXP expands signatures into instances, families, hypergraphs, theories, algorithms, prototypes, and codices.

## CVCD

CVCD means controlled computation by compressed virtual decomposition:

```text
compute on signatures first; decompress only where needed.
```

Operational form:

```text
X -> LOG(X) -> virtual test -> local EXP_delta -> OAK
```

## OAK status

Every motif is classified as:

- O: observed,
- A: anchored by definition,
- K: known or verified,
- S: speculative but testable,
- R: refuted,
- N: noise or non-relevant.

## Prototype path

Suggested next implementation files:

- sage_tristan/hgfm_prime_graph.py
- schemas/prime_tensor_packet.schema.json
- reports/prime_tensor_oak_report.md

## Canon summary

```text
prime -> tensor -> signature -> hyperedge -> motif -> compression -> OAK -> codex -> generator
```

This document is a scaffold. Promotion requires examples, tests, executable prototypes, and explicit OAK classification.
