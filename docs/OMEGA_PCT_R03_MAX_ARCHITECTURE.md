# Ω‑PARTICULES‑CHAMPS‑T∞ R0.3 MAX

## Executable theory-space compiler

R0.3 MAX moves Ω‑PCT∞ from a compact particle catalogue and QED reference
pipeline toward a typed, streaming compiler for spaces of particle–field
models. It does **not** claim a new law of nature. It creates machinery for
turning a proposed symmetry and field content into reviewable operators,
structural consistency findings, falsifiers, provenance bundles and finite
resource-governed campaigns.

## Delivered tranche

The first R0.3 tranche implements six coupled layers:

1. **Scientific types** — epistemic status, ontology level, fields, charges,
   parameters, operators, falsifiers, uncertainty, provenance and domains.
2. **Symmetry compiler** — parsing of common compact group identifiers,
   representation metadata for standard representations, exact rational U(1)
   anomaly sums, SU(N) cubic anomaly checks where representation data are
   supported, and SU(2) Witten-parity diagnostics.
3. **Lagrangian‑IR** — JSON ingestion, exact rational mass dimensions,
   U(1)-charge accounting, deterministic fingerprints, operator expressions
   and a machine-readable equation-of-motion variation IR.
4. **Operator grammar** — lazy generation of scalar monomials with dimension,
   fermion-parity and U(1)-invariance pruning. The generator has no permanent
   total-item cap; finite runs use real resource budgets.
5. **Candidate factories** — scalar portal, kinetically mixed dark vector and
   vectorlike-fermion research candidates. Every candidate is explicitly
   hypothetical and carries rejection criteria.
6. **OAK and campaigns** — twelve validation gates, disk-backed deduplication,
   JSONL sharding, SQLite indexing, checkpointing, failure isolation and M⁻.

## Scientific boundary

The compiler performs conservative structural checks. It does not replace:

- a full symbolic tensor algebra system;
- loop-level renormalization;
- a complete anomaly package for arbitrary representations;
- lattice QCD;
- event generation or detector simulation;
- global fits to experimental data;
- experimental replication.

Unsupported representations and missing numerical backends are reported as
unresolved. They are never silently treated as valid.

## Typed theory object

A theory is represented as

```text
TheorySpec(
  gauge_groups,
  fields,
  parameters,
  operators,
  falsifiers,
  domain,
  provenance,
  epistemic_status
)
```

Every field specifies a Lorentz representation, canonical mass dimension,
ontology level, chirality and gauge charges. Every operator is a product of
field factors with multiplicity, conjugation and derivative count.

## Exact dimensions and charges

Mass dimensions and U(1) charges use rational arithmetic. This avoids converting
simple values such as `1/3` or `3/2` into floating-point approximations during
structural validation.

For an operator

```text
O = product_i D^(d_i) Phi_i^(n_i)
```

R0.3 computes

```text
dim(O) = sum_i n_i dim(Phi_i) + sum_i d_i
```

and, for every declared U(1),

```text
Q(O) = sum_i sign(conjugation_i) n_i Q(Phi_i).
```

The operator fails the U(1) gate when the exact sum is nonzero.

## Anomaly checks

The symmetry compiler computes, for supported chiral spectra,

```text
A[U(1)^3] = sum_left d_spectator q^3 - sum_right d_spectator q^3
A[grav^2 U(1)] = sum_left d_spectator q - sum_right d_spectator q
```

It also evaluates supported SU(N) cubic coefficients and the parity of chiral
SU(2) doublets. Arbitrary irreducible representations require a future
representation backend and remain explicitly unresolved.

## Operator generation

`generate_scalar_monomials` is lazy. It does not allocate the full combinatorial
space. Candidates are pruned before emission according to:

- maximum campaign operator dimension;
- even fermionic parity for a bosonic scalar candidate;
- exact U(1) invariance;
- deterministic deduplication;
- optional quality floor;
- optional time and byte budgets.

A dimension or arity selected for one campaign is a search-domain choice, not a
permanent Ω‑PCT ceiling.

## Candidate factories

### Scalar portal

The scalar portal factory emits a typed Higgs–scalar interaction candidate,
parameter bounds and falsifiers such as excluded parameter regions or an
unstable scalar potential.

### Dark vector

The dark-vector factory emits a kinetically mixed U(1) candidate, including the
new vector field, kinetic-mixing operator, mass and mixing parameters, and
constraints that can reject a point or an inconsistent completion.

### Vectorlike fermions

The vectorlike factory streams combinations of color representation, weak
representation and hypercharge. The vectorlike chirality assignment cancels
left-minus-right perturbative gauge anomalies by construction, while all
phenomenological claims remain unvalidated.

## Twelve OAK gates

The report contains the fixed semantic gates:

1. syntax;
2. typing;
3. dimensions;
4. symmetry;
5. hermiticity and positivity;
6. conservation;
7. quantum consistency;
8. known limits;
9. numerics;
10. data;
11. falsification;
12. replication.

A structural pass is not a scientific confirmation. Gates without the required
backend remain false or warning-marked rather than being fabricated.

## Versioned PDG-style absorption

The absorber accepts an explicit upstream payload and records:

- edition;
- cutoff date;
- source locator;
- SHA‑256 of the complete source payload;
- accepted and quarantined counts;
- one digest per raw record.

Duplicate identifiers, missing identifiers and malformed values go to
`quarantine.jsonl`. No previous snapshot is overwritten implicitly.

## Unbounded campaign architecture

`CampaignRunner` consumes any iterable and stores accepted objects in adaptive
JSONL shards. It uses SQLite for persistent fingerprint deduplication and emits
atomic checkpoints.

There is no built-in `MAX_MODELS`, `MAX_PARTICLES` or `MAX_ADDITIONS`. A finite
run may stop because of:

- elapsed wall time;
- produced bytes;
- accumulated failures;
- an explicit quality floor;
- an external stop signal;
- exhaustion of the source.

This implements the rule:

```text
no permanent ceiling AND every execution remains governed
```

## M⁻ failure memory

Item-level failures do not terminate an entire campaign. The runner writes the
failing sequence, exception type, error and item into `m_minus.jsonl`. This is
an anti-dataset for subsequent generator and validator improvements.

## Commands

```bash
python -m omega_pct_t.r03max candidate scalar-portal
python -m omega_pct_t.r03max candidate dark-vector
python -m omega_pct_t.r03max compile path/to/theory.json
python -m omega_pct_t.r03max oak path/to/theory.json
python -m omega_pct_t.r03max absorb-pdg payload.json \
  --edition 2026 \
  --cutoff-date 2026-01-15 \
  --source-locator version-pinned-source \
  --output-dir generated/omega_pct_t/pdg-2026
```

## Next executable fronts

The next high-value fronts are:

1. arbitrary Lie-representation backend with Dynkin labels;
2. symbolic Lorentz-index contraction and hermiticity proofs;
3. Standard Model chiral spectrum fixture with exact anomaly cancellation;
4. EFT operator-basis generation modulo integration by parts and equations of
   motion;
5. process compiler from operators to interaction legs;
6. interfaces to established matrix-element and event-generation tools;
7. version-pinned experimental-constraint bundles;
8. blinded injected-signal OAKBench;
9. Pareto model comparison with Bayes‑Tristan and U²;
10. distributed campaign execution with proof-carrying shards.

## Canonical claim

R0.3 MAX is not valuable because it creates many names. It is valuable only if
it increases the rate at which malformed, inconsistent, excluded or
non-falsifiable models are rejected while preserving reproducible candidates
that deserve more expensive calculation or experiment.
