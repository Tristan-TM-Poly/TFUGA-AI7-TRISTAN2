# Experimental program — Ω-MYCELIAL-SYSTEMS-CALCULUS-T

All campaigns begin as **planned**. No result is implied until an executable run, configuration, provenance and uncertainty record exist.

Constitutional separation:

```text
synthetic mechanics != empirical evidence
historical replay != prospective validation
GitHub CI PASS != scientific claim validated
structural graph count != human maintenance cost
fixture oracle != measured detector accuracy
```

Every experiment must emit a machine-readable receipt containing:

```text
experiment_id
protocol_version
preregistered_at_or_commit
source_sha_set
baseline_ids
candidate_id
random_seed_or_determinism_note
measurements
uncertainty
failures
limitations
evidence_origin
status = PASS | HOLD | FAIL
```

## EXP-001 — Coordination scaling court

### Research question

When does capability-registry routing reduce coordination burden relative to manual all-to-all coupling and simpler integration baselines?

### Null hypothesis

After accounting for registry maintenance, contract churn, runtime routing and human intervention, the capability-centered design provides no material coordination advantage over the strongest simpler baseline.

### Baselines

1. explicit pairwise integration graph;
2. static dependency graph;
3. service/capability registry without executable hyperedges;
4. centralized monorepo/build-graph style integration;
5. proposed dynamic capability graph.

### Independent variables

- repository count `N`;
- capability count `C`;
- provider multiplicity per capability;
- consumer count per capability;
- schema/contract change rate;
- repository churn;
- task arrival rate;
- fraction of cross-repository tasks.

### Structural preflight

For an explicit complete undirected pairwise model:

```text
E_pairwise = N(N-1)/2
```

For a single-hub registration model:

```text
E_hub = N
```

These counts are graph identities under the stated models only. They are not evidence that real maintenance cost follows either curve.

### Measurements

- declared integration relations;
- configuration edits after controlled changes;
- failed contract tests;
- routing latency;
- compute overhead;
- number and duration of human interventions;
- recovery/rollback effort;
- orphan/duplicate capability rate.

### Experimental design

Run identical task/change traces across increasing `N` and `C`. Use deterministic synthetic traces first to validate mechanics, then historical replay, then prospective observed tasks if available. Keep task traces fixed across baselines.

### Promotion rule

A superiority claim remains HOLD unless the proposed system beats at least one strong simpler baseline on the preregistered primary coordination metric without causing a non-compensatory regression on correctness, reproducibility or human intervention.

## EXP-002 — Capability substitution court

### Research question

Can two providers implementing the same Capability IR be substituted without changing consumers beyond declared adapter/configuration boundaries?

### Null hypothesis

Provider-independent capability contracts do not reduce consumer modification or semantic breakage relative to repository-specific integration.

### Intervention factors

- implementation language/runtime;
- algorithm/provider identity;
- latency;
- output accuracy/quality;
- unit representation;
- failure mode;
- version and schema evolution.

### Substitution residual

For before/after provider observations define

```text
Delta_sub = (
  semantic_type_changed,
  unit_changed,
  quality_delta,
  latency_delta,
  cost_delta,
  consumer_edits,
  adapter_edits,
  contract_violations
)
```

### Measurements

- number of consumer source edits;
- number of configuration/adapter edits;
- contract violations;
- semantic/unit divergence;
- benchmark delta;
- recovery time after failed substitution.

### Negative controls

- intentionally incompatible semantic type;
- same software type but incompatible units;
- provider advertising the contract while violating a required bound;
- stale evidence receipt.

### Promotion rule

A substitution claim is supported only for the tested capability family and contract versions. No universal provider-interchangeability claim is allowed.

## EXP-003 — Theory-code divergence court

### Research question

Which divergences are detected by ordinary Software CI, Semantic CI, Scientific CI and OAK?

### Null hypothesis

Additional semantic/scientific/OAK gates provide no useful defect-detection gain after accounting for false positives, runtime and review cost.

### Injected defect families

1. syntax/API break;
2. semantic type mismatch;
3. unit mismatch;
4. convention change with type unchanged;
5. missing baseline;
6. missing negative control;
7. missing uncertainty;
8. stale evidence;
9. changed theoretical assumption;
10. unsupported conclusion;
11. provenance break;
12. reproducibility-seed omission.

### Blinded benchmark design

A defect generator creates commit-addressed variants. Detector runners receive only the candidate variant, not the defect label. The answer key is revealed only after all detector receipts are frozen.

### Metrics

- per-family detection rate;
- false-positive rate on clean controls;
- precision/recall where defined;
- time-to-detection;
- compute cost;
- human review minutes;
- explanation localization quality;
- severity-weighted missed-defect count.

### Ablations

Compare:

```text
Software CI
Software + Semantic
Software + Scientific
Software + Semantic + Scientific
Software + Semantic + Scientific + OAK
```

### Promotion rule

`CLM-SEMCI-001` remains HOLD unless detection gain survives clean controls and the added gates do not impose an unbounded false-positive/review burden.

## EXP-004 — Reuse-first vs generate-first

### Research question

Does `SEARCH → REUSE → ADAPT → GENERATE` reduce duplicate semantic implementations without degrading verified quality?

### Null hypothesis

Reuse-first provides no material improvement in duplication, maintainability or review effort once search/adaptation overhead is included.

### Task set

Use a frozen set of implementation/research tasks drawn from several domains. Each task must have enough repository context for a genuine reuse opportunity to be possible but not guaranteed.

### Arms

- Arm A: generate-first; repository search occurs only after a candidate solution exists.
- Arm B: reuse-first; corpus search and similarity/dedup review occur before generation.

### Measurements

- semantic duplicate count after review;
- new files/modules created;
- reused existing symbols/modules;
- lines changed;
- test coverage/detected defects;
- wall-clock and tool-call cost;
- human review effort;
- subsequent maintenance edits on follow-up changes.

### Counterfactual caution

Tasks must be randomized or matched; historical cases alone cannot identify a causal method effect.

## EXP-005 — Tristan GitHub empirical case study

### Research question

How do capabilities, claims, evidence, PRs, negative memory and reusable components actually evolve across the authorized repository history?

### Corpus layers

At minimum include, when accessible:

- `TFUGA-AI7-TRISTAN2`;
- `TTM-TFUGA-AI7-TRISTAN2`;
- merged thesis-factory history;
- Capability OS lineage;
- Living Factory R1/R2 lineage;
- Research Self-Model lineage;
- claims/evidence/M-minus artifacts relevant to the thesis.

### Temporal objects

```text
Repository
Commit
PullRequest
File/Symbol
Capability
Claim
EvidenceReceipt
Test/Benchmark
M-plus/M-minus/M-unknown
```

### Analyses

- temporal capability graph;
- capability genealogy;
- first reuse and reuse depth;
- duplicate emergence and later convergence;
- M-minus propagation;
- crystallization/promotion rate;
- theory-code drift episodes;
- PR-to-capability traceability;
- survival of claims under later evidence;
- cross-repository transfer.

### Causal boundary

Repository history is observational. It can support chronology, provenance, lineage and association. It cannot by itself establish causal superiority of a research operator or architecture.

## EXP-006 — Mycelial fixed-point reconstruction court

This sixth campaign is added because the source PDF defines a concrete self-hosting/fixed-point criterion.

### Research question

If only canonical schemas, manifests, capability graphs, tests, compilers and minimal seed documents are retained, how much of the ecosystem can be reconstructed without hidden state?

### Reconstruction protocol

1. freeze a source snapshot;
2. define a minimal retained seed set;
3. place reconstruction in an isolated clean-room workspace;
4. rebuild generated indexes/plans/artifacts using declared compilers only;
5. compare reconstructed and source systems using a typed equivalence ledger;
6. record every missing implicit dependency as M-minus.

### Metrics

- reconstructible capability fraction;
- reconstructible test fraction;
- claim/evidence trace recovery;
- semantic contract recovery;
- hidden-dependency count;
- byte-identical artifacts where determinism is expected;
- functionally equivalent artifacts where byte identity is not expected;
- human intervention count.

### Non-claim

A high reconstruction score is evidence of compressibility/reproducibility under the tested seed set. It is not evidence of autonomous intelligence, general self-replication or scientific correctness.

## EXP-007 — Theory → Code → Evidence → RevisedTheory round-trip

### Research question

Can the bidirectional compiler retain explicit theory semantics through implementation and evidence updates, and localize residual disagreement?

### Protocol

1. choose a bounded formal theory card;
2. compile obligations and implementation scaffold;
3. execute tests/benchmarks or attach explicit HOLDs;
4. reconstruct the implicit theory from resulting artifacts;
5. compare original and reconstructed theory claim-by-claim;
6. revise the theory only from explicit evidence/residuals;
7. measure `Delta_T` as a vector, not an unqualified scalar.

### Residual dimensions

```text
Delta_T = (
  definitions,
  assumptions,
  claims,
  units_types,
  evidence,
  limits,
  provenance
)
```

### Promotion rule

Round-trip consistency is supported only on tested theory families. A low residual does not imply that the theory is true; it means only that theory, implementation and recorded evidence are mutually consistent under the chosen comparison contract.

## Evidence ladder for all campaigns

```text
S0 protocol only
S1 deterministic mechanics fixture
S2 historical replay
S3 prospective internal observation
S4 independent/clean-room replay
S5 external replication when applicable
```

No later status may be inferred from an earlier one. Negative and HOLD results remain part of the thesis evidence bundle.
