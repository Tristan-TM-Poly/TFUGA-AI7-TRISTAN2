# R0.3 design invariants

## Pocklington gate

For `N > 1`, let the known, proven factor product of `N - 1` be

```text
F = product(q_i ** e_i).
```

R0.3 accepts a certificate only when:

- `F` divides `N - 1`;
- every distinct `q_i` is independently proven prime by deterministic u64 testing or a recursive child certificate;
- `F > floor(sqrt(N))`;
- for every distinct `q_i`, a witness `a_i` satisfies
  `a_i ** (N - 1) = 1 (mod N)`;
- `gcd(a_i ** ((N - 1) / q_i) - 1, N) = 1`;
- the canonical SHA-256 digest matches;
- novelty, record and economic-value flags remain false.

## Provenance gate

Leaves are domain-separated with byte `0x00`; internal nodes are domain-separated with byte `0x01`. Odd levels duplicate the final hash. Every checked artifact retains its leaf index, sibling path, root and leaf count.

## Lease gate

- claims occur under `BEGIN IMMEDIATE`;
- one pending task can be leased to at most one owner;
- only the current owner with a non-expired lease may renew or finish;
- expired leases return to `pending` before reassignment;
- completed or failed states are terminal in R0.3;
- every transition appends an event row;
- WAL and `PRAGMA integrity_check` are exercised in tests.

This is a lease protocol, not distributed consensus. Multiple workers still trust the same SQLite database and host filesystem.

## Precedence gate

The adapter is deliberately offline and snapshot-bound. Its strongest positive statement is:

> the value was not present in these exact supplied snapshots.

`global_novelty_claim_allowed` is hard-coded to false in R0.3. Future live adapters must preserve source URL, capture time, license, query, coverage semantics, response hash and failure state.

## Cross-language gate

Python is the reference vector producer. C++ uses `unsigned __int128`; Rust uses `u128`. CI compiles both kernels and requires byte-equivalent JSON values for:

- deterministic Miller–Rabin over unsigned 64-bit integers;
- modular exponentiation;
- radix-2 NTT convolution modulo `998244353`.
