# R0.4 design invariants

## 1. Recursive proof graph

A proof graph is accepted only when:

1. the graph hash matches its canonical JSON;
2. the root exists;
3. node identifiers match their map keys;
4. every child reference targets an existing node;
5. every referenced child proves the corresponding factor prime;
6. every Pocklington certificate verifies after child reconstruction;
7. the graph is acyclic;
8. every node is reachable from the root;
9. novelty and record flags remain false.

The graph representation separates certificate content from child references. This permits deduplication and cycle detection without weakening the underlying Pocklington verification.

## 2. Residue compiler

For a Proth candidate

```text
P(k,n) = k*2^n + 1,
```

and an odd small prime `l`, compositeness is forced when

```text
k = -2^(-n) mod l.
```

R0.4 compiles these forbidden residue classes once, binds them by SHA-256 and applies them in finite segments. A survivor is only “not rejected by these divisors”; it is not declared probable prime or prime.

## 3. Transparency log

Each entry binds:

```text
sequence, kind, payload_hash, previous_hash
```

into `entry_hash`. A checkpoint commits to a finite prefix through both the chain head and a domain-separated Merkle root.

An unsigned checkpoint provides integrity evidence only. An Ed25519/OpenSSL signature provides authenticity relative to the supplied public key. Key generation, storage, rotation and revocation remain external governance responsibilities.

## 4. External verifier adapter

The adapter:

- hashes imported bytes before execution;
- requires an existing absolute executable path;
- invokes an argument vector directly, never a shell;
- enforces a bounded timeout;
- records executable, stdout and stderr hashes;
- distinguishes import, tool acceptance and institutional verification.

It does not parse arbitrary verifier semantics or automatically trust a program because it exits with code zero.

## 5. Compute budget

Every accepted observation must remain under the effective limits after the policy reserve is removed. The state becomes:

```text
open          utilization < 80%
backpressure  80% <= utilization < 100%
halt          utilization >= 100%
```

Costs and energy are user-supplied evidence. They are not invoices, financial projections or environmental certifications.
