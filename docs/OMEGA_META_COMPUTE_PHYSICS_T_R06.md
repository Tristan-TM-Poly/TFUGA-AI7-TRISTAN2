# Ω-META-COMPUTE-PHYSICS-T∞ — R0.6 Universal Fleet Intelligence

Status: **D-MVP candidate / R0.6**. Static, commit-addressed planning layer. No arbitrary target-code execution.

## 1. Goal

R0.6 turns the R0.5 fleet infrastructure into a provenance-preserving map of code across repositories and languages:

```text
repository@commit
-> Snapshot Ledger
-> language adapters
-> Source Genomes
-> Python Complexity-IR
-> static Call Graph
-> risk preflight
-> fixture registry
-> benchmark-contract plans
-> external reviewed execution boundary
-> measured ResourceSamples
-> Complexity Diff
-> Regression Ledger
```

The key change is that every future performance claim can be traced back to an exact repository revision and a reviewable chain of evidence.

## 2. Snapshot Ledger

`omega_compute_physics_t/snapshot_ledger.py`

A `RepositorySnapshot` contains:

- repository identity;
- pinned commit SHA;
- file path;
- byte size;
- content identity (`git blob sha` when records come from Git, SHA-256 for a local checkout);
- extension counts;
- total inventoried bytes.

`compare_snapshots(old, new)` classifies added, removed, changed and unchanged files.

OAK invariant:

```text
changed blob != semantic regression != performance regression
```

A changed blob is only a trigger for re-analysis.

## 3. Static Call Graph

`omega_compute_physics_t/call_graph.py`

R0.6 links Python `FunctionIR` objects using conservative name resolution.

Outputs include:

- resolved call edges;
- unresolved call targets;
- fan-in / fan-out;
- strongly connected components;
- recursive components.

The graph is useful for determining whether a local optimization can propagate through many callers, and for later DAG cost composition.

OAK invariant: Python dynamic dispatch, reflection, imports, monkey patching and decorators can invalidate a purely static graph.

## 4. Fixture Registry

`omega_compute_physics_t/fixture_registry.py`

A benchmark is not meaningful unless its inputs are defined. `FixtureSpec` records:

- fixture id;
- input schema;
- benchmark axes;
- determinism;
- whether inputs are pure data;
- file/network requirements.

Automatic planning rejects nondeterministic, non-pure or network-backed fixtures.

R0.6 provides only metadata specifications. A trusted external adapter must implement the actual fixture.

## 5. Static Risk Preflight

`omega_compute_physics_t/risk_preflight.py`

The preflight deliberately over-approximates potential benchmark risk by looking for indicators of:

- network access;
- credentials/secrets;
- mutating filesystem operations;
- subprocess/external side effects;
- privileged/system operations.

It emits `RiskFinding` evidence with symbol and source line, then maps that evidence onto the R0.5 `BenchmarkRisk` vector.

OAK invariant:

```text
no static risk flag != safe code
```

The scanner can have false positives and false negatives and is never a sandbox certification.

## 6. Benchmark Contract Planner

`omega_compute_physics_t/contract_planner.py`

`plan_contract(...)` binds:

```text
Stage A seed
+ pinned commit
+ deterministic fixture spec
+ explicit axis values
+ static risk report
-> BenchmarkContract candidate
```

The planner always leaves `trusted_checkout=False`.

Therefore automatically generated contracts are intentionally non-executable until a separate review or trusted infrastructure adapter approves the checkout.

## 7. Cross-commit Regression Ledger

`omega_compute_physics_t/regression_ledger.py`

A `ComplexityDiffReport` can be transformed into a `RegressionEvent` containing:

- old/new commit;
- resource target;
- regression fraction;
- maximum relative increase;
- mean relative change;
- minimum certified-domain overlap;
- severity;
- whether rebenchmarking is required.

Severity thresholds are operational policy, not mathematical theorem thresholds.

OAK invariant:

```text
resource regression != asymptotic complexity-class regression
```

## 8. Multi-language Source Genomes

`omega_compute_physics_t/language_adapters.py`

Python uses the built-in AST and Complexity-IR.

R0.6 also recognizes common source extensions for:

- C;
- C++;
- JavaScript;
- TypeScript;
- Rust;
- Go;
- Java;
- C#;
- Julia;
- R;
- shell.

Non-Python languages currently use bounded lexical fingerprints: LOC, function-like blocks, loop tokens, branch tokens, call-like tokens, allocation tokens and brace depth.

These lexical fingerprints make non-Python code visible to the Fleet Atlas immediately, but they are intentionally marked `heuristic`. Future R0.7+ adapters should replace them with parser/compiler/Tree-sitter evidence where useful.

## 9. Universal Fleet Scan

`omega_compute_physics_t/universal_fleet.py`

For each local pinned checkout:

```text
files
-> SHA-256 static snapshot
-> language detection
-> SourceGenome per supported source file
-> Python Complexity-IR
-> Python CallGraph
-> repository report
```

Across repositories:

```text
UniversalRepositoryReport[]
-> UniversalFleetReport
```

The fleet report includes source-file counts, Python IR function counts and language counts across the entire fleet.

No repository module is imported or executed.

## 10. R0.6 CLI

```bash
python -m omega_compute_physics_t.r06_cli snapshot ./repo \
  --repository Tristan-TM-Poly/example \
  --commit <sha>

python -m omega_compute_physics_t.r06_cli risk path/to/module.py

python -m omega_compute_physics_t.r06_cli call-graph a.py b.py

python -m omega_compute_physics_t.r06_cli universal-fleet \
  --repo A=/checkouts/A --commit A=<shaA> \
  --repo B=/checkouts/B --commit B=<shaB>
```

All R0.6 CLI operations are static.

## 11. Evidence schema

`complexity_atlas/evidence_schema_v0_6.json`

The schema provides a common envelope for:

- repository snapshots;
- snapshot diffs;
- call graphs;
- fixture registries;
- risk preflights;
- benchmark contract plans;
- regression ledgers;
- source genomes;
- universal repository/fleet reports.

Schema validity is not evidence of scientific truth or runtime safety.

## 12. Fleet-wide operating loop

The intended loop for all repositories becomes:

```text
PIN
-> SNAPSHOT
-> SCAN
-> LINK
-> RISK
-> PLAN FIXTURE
-> PLAN CONTRACT
-> REVIEW
-> MEASURE EXTERNALLY
-> FIT/VALIDATE
-> DIFF
-> LEDGER
-> REPRIORITIZE
```

This creates a chronological computational atlas rather than isolated benchmark results.

## 13. OAK promotion ladder

### Static evidence

- file/blob changed;
- SourceGenome changed;
- Complexity-IR changed;
- call graph changed;
- static risk changed.

### Empirical evidence

Requires controlled measurement:

- wall/CPU/memory change;
- resource-law change;
- crossover/regime change;
- regression/improvement fraction.

### Mechanistic claim

Requires intervention/counters/independent evidence.

### Asymptotic mathematical claim

Requires algorithmic or formal proof.

No layer is automatically promoted to the next one.

## 14. Why this matters for the full Tristan GitHub fleet

R0.6 makes the system reusable at repository scale because the unit of analysis is no longer only a Python function. It can now represent:

```text
owner
-> repository
-> commit
-> file
-> language
-> function/structural unit
-> dependency
-> risk
-> benchmark plan
-> resource evidence
-> regression history
```

That hierarchy maps naturally into HGFM Zoom/Dezoom and can later become a living cross-repository compute atlas.

## 15. R0.7 frontier

Highest-value next steps:

1. ingest complete Git trees for every pinned repository into portable Snapshot Ledgers;
2. add exact parser adapters for the non-Python languages actually present in the fleet;
3. resolve Python imports and qualified call targets across modules;
4. add change-impact propagation from snapshot diff -> call graph -> benchmark priority;
5. synthesize fixture requirements from signatures/type hints without inventing semantics;
6. connect an explicitly authorized execution/sandbox adapter;
7. run Stage B only for pure deterministic low-risk kernels;
8. store measured cross-commit resource evidence as a temporal HGFM;
9. add confidence-debt and benchmark half-life policies;
10. create fleet-wide optimization ROI ranking.

## 16. Hard boundaries

R0.6 does **not** claim:

- complete static call resolution;
- semantic equivalence across languages;
- runtime complexity from lexical tokens;
- security from static risk scanning;
- executable correctness from fixture metadata;
- performance regression from changed source alone;
- asymptotic complexity from empirical resource measurements.

Those boundaries are features of the architecture, not missing disclaimers.
