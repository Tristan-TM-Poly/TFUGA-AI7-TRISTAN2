# Ω-DISCOVERY-PATH-COMPILER-T∞ — R0.4

Status: **software architecture + executable IR under OAK validation**.

R0.4 changes the fundamental object of GreatSages from a named historical actor or isolated discovery to an auditable **trajectory between epistemic states**.

```text
EpistemicState
  -> operator
  -> EpistemicState
  -> operator
  -> ...
  -> target state
```

This is a model of knowledge transformation. It is **not** a claim that the encoded sequence uniquely reconstructs a historical person's mental process.

## 1. Core object

A path is modeled as:

\[
\pi = E_0 \xrightarrow{O_1} E_1 \xrightarrow{O_2} \cdots \xrightarrow{O_n} E_n.
\]

Each `EpistemicState` carries:

- year;
- admitted knowledge identifiers;
- representations;
- evidence identifiers;
- open problems;
- uncertainty;
- epistemic debt;
- provenance identifiers.

Each `PathStep` carries:

- a known cognitive operator;
- input/output state identities;
- representation before/after;
- evidence used;
- claims produced;
- a resource-cost vector;
- a residual vector;
- uncertainty before/after;
- an explicit note.

## 2. Cost is multi-dimensional

R0.4 refuses to equate a short path with a good path.

The executable `ResourceCost` contains:

- computation;
- conceptual transformation;
- evidence acquisition/use;
- uncertainty burden;
- epistemic debt;
- representation loss;
- risk.

The current weighted total is a **software heuristic**, not a historical or psychological law.

Future releases may learn or task-condition these weights, but any learned score must remain calibrated against external outcomes.

## 3. Residuals are first-class

Every path step preserves unresolved structure via `ResidualVector`:

- logical residual;
- empirical residual;
- representation residual;
- provenance residual;
- uncertainty residual.

A path is therefore never represented only by what it solved. It also records what remains unexplained.

This is the DiscoveryPath equivalent of Tristan's M− / residue discipline.

## 4. OAK path audit

`audit_path()` checks:

1. exact state-step continuity;
2. monotone chronology;
3. registered operators only;
4. target withheld from the initial state;
5. target/future descendants absent from step evidence;
6. terminal state contains the target;
7. terminal uncertainty does not exceed initial uncertainty.

A passing result receives:

```text
VALID_SOFTWARE_MODEL
```

not:

```text
HISTORICALLY_TRUE
```

Failure produces `QUARANTINE`.

## 5. Gauss/Ceres is a fixture, not a mental simulation

The first R0.4 fixture uses the already-seeded 1801 Ceres target.

Its path is explicitly tagged `ClaimClass.RECONSTRUCTION` and includes:

```text
representation_switch
 -> approximation_residual
 -> invariant_search
```

The encoded sequence tests the IR. It does not assert that this is the unique documented causal route followed by Gauss.

## 6. Anti-Sage path parallax

R0.4 also generates an adversarial branch replacing the first representation switch with:

```text
anti_switch_stay_native
```

`compare_paths()` reports:

- shared operators;
- left-only operators;
- right-only operators;
- shared representations;
- cost delta;
- residual delta.

This establishes the first executable form of:

\[
\text{intelligence collective} = \text{consensus} + \text{parallax}.
\]

The purpose is not to select a winner by rhetoric. Future versions must compare paths on controlled external tasks.

## 7. Path composition

If:

\[
\pi_1:A\to B
\]

and:

\[
\pi_2:B\to C,
\]

then `compose_paths()` permits:

\[
\pi_2\circ\pi_1:A\to C
\]

only when the boundary state is exactly identical.

This is the first executable step toward a category/path algebra of scientific transformations.

## 8. Machine-readable schema

`schemas/discovery_path_r04.schema.json` mirrors the runtime structure and is CI-checked against the canonical `ClaimClass` values.

Schema conformance means only:

```text
this object satisfies the declared structural contract
```

It does not establish truth, novelty, authorship, safety, causality, or IP ownership.

## 9. Relation to Ω-DISCOVERY-KERNEL-T∞

The repository already contains a mature event/evidence ledger.

The two objects are deliberately different:

```text
DiscoveryPath
  = modeled program / trajectory / candidate transformation path

DiscoveryLedger
  = append-only workflow/evidence event record
```

R0.4 adds `discovery_path_kernel_bridge.py` to project a path into the existing Ω64 event envelope:

```text
ObservationEvent
 -> ClaimEvent
 -> GeneratorCandidate ...
 -> ExperimentSpec
 -> ResultPacket
 -> OAKTransition
```

The bridge validates the existing event contracts and parentage while retaining:

```text
historical_causation_certified = false
```

A later release may append these events to a full closed-loop ledger only after the ledger's own gates are satisfied.

## 10. What R0.4 actually proves

When CI is green, R0.4 proves only software properties such as:

- deterministic path hashing;
- bounded cost/residual fields;
- structural continuity;
- anti-leakage evidence gating;
- operator registry enforcement;
- composability at identical boundaries;
- event-envelope compatibility;
- machine-readable schema/runtime alignment.

It does **not** prove:

- a historical cognitive process;
- causal effectiveness of a cognitive operator;
- scientific correctness of a generated discovery;
- novelty;
- superiority to another research method.

## 11. Negative memory M−

R0.4 adds the following permanent anti-errors:

**M−R04-1 — Path = history.**

A valid path model is not a certified historical causal sequence.

**M−R04-2 — Shortest = best.**

Path length alone ignores uncertainty, evidence, representation loss, residuals and risk.

**M−R04-3 — Operator correlation = causal power.**

Historical co-occurrence cannot establish that an operator causes success.

**M−R04-4 — Schema = truth.**

Machine-readable validity is structural only.

**M−R04-5 — Event record = scientific certification.**

The discovery ledger records workflow/evidence; it does not turn a reconstructed path into historical fact.

**M−R04-6 — Ignore failed branches.**

Path comparison must preserve adversarial alternatives and residuals rather than only the selected route.

## 12. Generation roadmap

R0.4 is intentionally a kernel, not a package explosion.

The next candidate generations are:

### R0.5 — Representation / Noether Compiler

Measure representation transforms using complexity change, information loss and invariant defect.

### R0.6 — Cognitive ISA / Program Search

Promote cognitive operators into a formal instruction set and search bounded operator programs with Anti-Sage duals.

### R0.7 — DiscoveryBench 2.0

Separate context leakage, retrieval/tool leakage and pretraining contamination; add synthetic/secret discovery tasks.

### R0.8 — Discovery Self-Model

Learn empirical associations between problem genomes, operator programs, costs and outcomes while preserving causal uncertainty.

### R0.9 — Human Knowledge Genome

Feed the path IR from multilingual, polycentric, source-traced actor/access/transmission graphs.

### R1.0 — Civilization Discovery OS

Unify source ingestion, HGFM, access/transmission, representation transforms, path compilation, OAK, benchmarks and research self-models.

None of these future names imply implemented capability until code + tests + OAK gates exist.

## 13. Canonical equation

The R0.4 doctrine is:

\[
\boxed{
\text{discovery}
= 
\text{state transformation path}
+ 
\text{evidence}
+ 
\text{residuals}
+ 
\text{cost}
+ 
\text{uncertainty}
}
\]

and:

\[
\boxed{
\text{better research}
\neq
\text{more generated ideas};
\qquad
\text{better research}
=
\text{better tested paths}.
}
\]
