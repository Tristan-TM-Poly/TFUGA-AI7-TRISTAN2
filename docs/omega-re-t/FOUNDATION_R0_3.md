# Ω-RE-T∞ R0.3 — Active, Causal and Multi-Domain Reconstruction Forge

## Status

R0.3 is an additive research expansion over the validated R0.1 and R0.2 kernels. It remains restricted to synthetic, owned, openly specified or expressly authorized systems. The package reconstructs bounded behavioral and causal model classes; it does not claim access to inaccessible internals.

## Epistemic doctrine

A reconstruction report must separate:

1. direct observation;
2. measurement with uncertainty;
3. derived quantity;
4. inferred model;
5. behavioral equivalence on a declared domain;
6. interventionally supported causal relation;
7. independent replication;
8. verification within a bounded domain.

High predictive fidelity is not proof of internal identity. Materializing a benchmark is not executing it. Passing software tests is not scientific validation.

## R0.3 engines

### 1. Bounded active Mealy learning

`active_learning.py` learns a finite behavioral quotient without enumerating every machine in a hypothesis universe. Access sequences are clustered using future-output signatures over a declared probe set. The report exposes the access depth, probe depth, membership-query count, finite validation domain and counterexamples.

The method is exact only on the tested domain. Unreachable states and distinctions requiring longer suffixes remain outside the claim.

### 2. Partial and nondeterministic machines

`nondeterministic.py` retains conflicting outputs and partial behavior explicitly. It supports:

- multiple initial states;
- partial transition relations;
- nondeterministic output traces;
- bounded trace equivalence;
- prefix-tree transducer inference;
- reachable-state analysis;
- determinism-violation reports.

Conflicting traces are not silently averaged or discarded.

### 3. Intervention-aware causal reconstruction

`causal.py` introduces directed acyclic causal graphs, interventions, treatment-effect estimates, mutual information and ranked edge candidates. Association-only edges are marked separately from interventionally supported edges.

The initial estimator is deliberately low-order and synthetic. It does not replace domain causal analysis, confounder control or experimental design.

### 4. Conservative format grammar inference

`grammar.py` infers delimited record structure from authorized examples. It estimates:

- delimiter consistency;
- field count;
- integer, float, hexadecimal, Boolean, enumeration and text fields;
- optionality;
- observed ranges;
- ambiguous enum-versus-text cases;
- rejected records.

The resulting grammar is a bounded compatibility hypothesis, not a claim about an inaccessible original parser.

### 5. Protocol-state reconstruction

`protocol.py` builds a prefix-tree protocol model from request/response traces. Equivalent terminal leaves may be merged, while conflicting responses remain explicit nondeterminism. The engine records latency ranges and proposes synthetic discriminating request sequences across competing models.

### 6. Hybrid systems

`hybrid.py` represents discrete modes with affine continuous dynamics and guarded transitions. It provides deterministic Euler simulation and small ridge-regularized affine fits for synthetic fixtures. It exposes residuals and identifiability warnings rather than silently promoting underdetermined parameters.

### 7. Version genealogy

`genealogy.py` reconstructs a minimum-distance ancestry hypothesis from features, behavior maps, timestamps and provenance. It supports roots, lineages, cycle prevention and regression localization. The inferred genealogy is parsimonious evidence, not definitive historical authorship.

### 8. Clean-room multi-agent separation

`cleanroom_agents.py` separates observer, specifier, implementer and auditor roles. Artifacts carry content digests and source-artifact links. The audit detects missing roles, restricted-material propagation, forbidden provenance paths and specification dependence on implementation artifacts.

### 9. Sharded campaigns and receipts

`sharding.py` defines deterministic shard plans, item digests, Merkle-style roots, chained shard receipts, checkpoints and pending-shard iteration. Logical cardinality remains separate from materialized, processed and validated cardinality.

## RE-64

R0.3 defines 64 parent fixtures:

- 16 mechanism families;
- four variants per family: minimal, ambiguous, noisy and boundary.

Families:

1. active automata;
2. partial and nondeterministic automata;
3. probabilistic mechanisms;
4. timed mechanisms;
5. causal graphs;
6. formats;
7. protocols;
8. hybrid systems;
9. low-order physical systems;
10. organizational processes;
11. version genealogies;
12. AI behavioral cartography;
13. clean-room pipelines;
14. residual mechanisms;
15. constraint systems;
16. sharded campaigns.

Every seed contains synthetic truth, observations, competing candidates, expected identifiability, controls, failure modes, authorization metadata and a deterministic digest.

## RE-1024

Sixteen perturbations are applied to every RE-64 seed:

1. baseline;
2. label permutation;
3. missing observation;
4. duplicate observation;
5. light noise;
6. moderate noise;
7. tight budget;
8. wide budget;
9. biased prior;
10. mixed versions;
11. missing provenance;
12. instrument offset;
13. timing jitter;
14. negative control;
15. unobserved region;
16. true model class omitted.

This creates 1,024 deterministic cases. The manifest must always preserve:

```text
logical_cases = 1024
materialized_cases = 1024
executed_cases = 0
software_tested_cases = 0
scientifically_verified_cases = 0
logical_space_is_not_execution = true
materialization_is_not_validation = true
```

A later campaign may update execution receipts in separate append-only artifacts; it must never rewrite the original frontier to imply execution.

## Test surface

R0.3 tests cover:

- membership-query caching;
- bounded active learning;
- nondeterministic trace preservation;
- bounded equivalence;
- causal DAG cycle rejection;
- intervention effects;
- mutual information;
- grammar inference and rejection;
- protocol replay and experiment proposals;
- hybrid simulation and affine fitting;
- genealogy and regression localization;
- clean-room contamination detection;
- shard receipt chains;
- RE-64 and RE-1024 cardinality;
- deterministic materialization;
- all CLI demonstrations.

## CLI

```bash
omega-re-r03 catalog
omega-re-r03 learn-demo
omega-re-r03 grammar-demo
omega-re-r03 protocol-demo
omega-re-r03 causal-demo
omega-re-r03 cleanroom-demo
omega-re-r03 genealogy-demo
omega-re-r03 frontier --materialize benchmarks/omega-re/re1024.json --shard-size 128
```

Direct module interface:

```bash
python -m omega_re_t.r03_frontier --verify-only
python -m omega_re_t.r03_frontier --output benchmarks/omega-re/re1024.json
```

## OAK gates

Promotion is blocked when:

- authorization is missing;
- a case claims external execution;
- a materialized fixture claims scientific verification;
- provenance is absent without a downgraded status;
- digest validation fails;
- duplicate case identifiers exist;
- a clean-room forbidden path exists;
- an intervention effect is inferred from association alone;
- active-learning equivalence is extended outside the tested domain;
- a version genealogy is presented as proven history;
- a hybrid fit is underdetermined;
- a generated cardinality is reported as completed work.

## Negative memory M−

R0.3 records the following recurring failure classes:

- state aliases caused by shallow probes;
- omitted true model class;
- nondeterminism forced into deterministic models;
- noise confused with stochastic dynamics;
- timing information discarded;
- association promoted as causality;
- under-sampled enumeration inferred as universal grammar;
- mixed protocol versions;
- continuous dynamics fit across mode boundaries;
- minimum-distance genealogy mistaken for authorship proof;
- clean-room contamination;
- broken receipt chains;
- benchmark materialization advertised as experiment execution.

## Next frontier

R0.4 should add probabilistic programs, symbolic state merging, active causal intervention design, richer context-free grammar inference, protocol version negotiation, nonlinear hybrid bases, Bayesian version genealogy, signed receipts, distributed campaign leases and separately executed RE-1024 software baselines.
