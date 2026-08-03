# Ω-PRIME-VALUE-T∞ R0.4 Plus Ultra

R0.4 turns the R0.3 single-certificate and worker primitives into a governed proof-publication fabric.

## Executable components

- recursive Pocklington certificate DAG with deduplication, reachability checks and cycle rejection;
- compiled residue-class programs for `k*2^n + 1`, executed as bounded segmented filters;
- SQLite/WAL append-only transparency log with hash chaining and Merkle checkpoints;
- optional Ed25519 checkpoint signing through the local OpenSSL executable;
- opaque Primo/ECPP artifact import with SHA-256 binding;
- explicit external verifier receipts executed without a shell;
- adaptive compute-budget ledger with reserved capacity and backpressure;
- deterministic R0.4 benchmark and JSON schemas.

## Quick start

```bash
python -m omega_prime_value_t.r04 benchmark \
  --output generated/omega_prime_value_t/r04-benchmark.json

python -m omega_prime_value_t.r04 compile-residues \
  --exponent-min 8 --exponent-max 20 --prime-bound 10000 \
  --output generated/omega_prime_value_t/residue-program.json

python -m omega_prime_value_t.r04 scan-residues \
  generated/omega_prime_value_t/residue-program.json \
  --exponent 20 --k-start 1 --k-stop 1048575 \
  --segment-size 65536 \
  --output generated/omega_prime_value_t/residue-receipt.json
```

Proof graph round trip:

```bash
python -m omega_prime_value_t.r04 build-proof-graph certificate.json --output proof-graph.json
python -m omega_prime_value_t.r04 verify-proof-graph proof-graph.json --output verification.json
```

External artifact import remains unverified unless an explicit verifier is supplied:

```bash
python -m omega_prime_value_t.r04 import-external certificate.out \
  --format primo --source-label local-primo-run \
  --output import-receipt.json
```

## Demonstrated recursive fixture

The R0.4 deterministic fixture proves:

```text
q = 9*2^65 + 1 = 332041393326771929089
N = 88*q + 1 = 29219642612755929759833
```

The proof for `N` references the proof for `q` as a child node. Small factors `2` and `11` are independently decided in the deterministic unsigned-64-bit domain.

## Boundary

R0.4 does not claim that either fixture is newly discovered, record-setting, economically exclusive or fit for cryptographic-secret generation. External verifier success records what one declared executable reported; it is not institutional independence. A signed checkpoint authenticates a log root under a particular key; it does not establish that the logged claims are true.
