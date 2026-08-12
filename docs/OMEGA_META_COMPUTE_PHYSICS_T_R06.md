# Ω-META-COMPUTE-PHYSICS-T∞ — R0.6 Universal Fleet Intelligence

Status: **D-MVP candidate / R0.6**. Commit-addressed, static-first fleet intelligence with evidence-aware revalidation and optimization planning. No arbitrary target-code execution.

## 1. Mother pipeline

R0.6 turns the R0.5 fleet infrastructure into a provenance-preserving computational map:

```text
repository@commit
-> Snapshot Ledger
-> multi-language Source Genomes
-> Python Complexity-IR
-> static Call Graph
-> Snapshot Diff
-> Change-Impact Propagation
-> static Risk Preflight
-> deterministic Fixture Registry
-> Benchmark Contract Plan
-> external reviewed execution boundary
-> ResourceSamples
-> validation + uncertainty
-> Complexity Diff
-> Regression Ledger
-> Confidence Debt
-> Optimization ROI
-> reprioritize
```

Every future performance claim can therefore be traced to an exact repository revision and a reviewable evidence chain.

## 2. Snapshot Ledger

`omega_compute_physics_t/snapshot_ledger.py`

A `RepositorySnapshot` records repository identity, pinned commit SHA, file path, byte size, content identity, extension counts and total inventoried bytes. Git-tree records can retain Git blob identities; local read-only checkouts use SHA-256.

`compare_snapshots(old, new)` classifies added, removed, changed and unchanged files.

OAK invariant:

```text
changed blob != semantic regression != performance regression
```

A changed blob is a trigger for re-analysis, not a performance conclusion.

## 3. Complexity-IR and Static Call Graph

`omega_compute_physics_t/complexity_ir.py` converts Python syntax into a hardware-independent operation inventory such as `LOAD`, `STORE`, `ARITH`, `COMPARE`, `INDEX`, `CALL`, `LOOP`, `BRANCH`, `ALLOC`, `COMPREHENSION`, `AWAIT` and `YIELD`.

`omega_compute_physics_t/call_graph.py` links `FunctionIR` objects using conservative name resolution and reports resolved call edges, unresolved call targets, fan-in/fan-out, strongly connected components and recursive components.

OAK invariant: Python dynamic dispatch, reflection, imports, monkey patching and decorators can make the runtime graph differ from the static graph.

## 4. Change-Impact Propagation

`omega_compute_physics_t/change_impact.py`

A `SnapshotDiff` can be propagated through the reverse static call graph:

```text
changed file
-> directly affected functions
-> callers at distance 1
-> callers at distance 2
-> ... bounded max_hops
```

Impact decays with graph distance and can be lightly weighted by fan-in. Changed files absent from the resolved graph remain explicit `unresolved_changed_files` rather than disappearing.

OAK invariant:

```text
static impact score != semantic impact != measured performance impact
```

## 5. Deterministic Fixture Registry

`omega_compute_physics_t/fixture_registry.py`

A `FixtureSpec` records fixture id, input schema, benchmark axes, determinism, pure-data status and file/network requirements. Automatic planning rejects nondeterministic, non-pure or network-backed fixtures. R0.6 ships only metadata specifications; a trusted external adapter must implement and validate actual target inputs.

## 6. Static Risk Preflight

`omega_compute_physics_t/risk_preflight.py`

The preflight deliberately over-approximates potential benchmark risk. It looks for indicators of network access, credentials/secrets, mutating filesystem operations, subprocess/external side effects and privileged/system operations.

It emits source-located `RiskFinding` evidence and maps it to the R0.5 `BenchmarkRisk` vector.

OAK invariant:

```text
no static risk flag != safe code
```

A clean risk report is never a sandbox certification.

## 7. Benchmark Contract Planner

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

Generated contracts deliberately retain `trusted_checkout=False`. Therefore they remain non-executable until an explicitly reviewed external infrastructure layer approves the checkout and invocation semantics.

## 8. Regression Ledger

`omega_compute_physics_t/regression_ledger.py`

A `ComplexityDiffReport` can become a `RegressionEvent` containing old/new commit, target resource, regression fraction, maximum relative increase, mean relative change, minimum certified-domain overlap, severity and rebenchmark decision.

OAK invariant:

```text
finite-domain resource regression != asymptotic complexity-class regression
```

## 9. Confidence Debt and Benchmark Half-Life

`omega_compute_physics_t/confidence_debt.py`

Freshness follows a configurable half-life proxy:

```text
freshness = 2^(-age_days / half_life_days)
```

Confidence debt combines staleness, calibration gap, certified-domain mismatch, code change and machine change. The result routes evidence into `fresh-enough`, `schedule-revalidation`, `high-revalidate` or `critical-revalidate`.

OAK invariant: confidence debt is a scheduling heuristic, not a posterior probability that a claim is false.

## 10. Evidence-aware Optimization ROI

`omega_compute_physics_t/optimization_roi.py`

Optimization priority is separated from remeasurement priority. A dimensionless value proxy combines:

```text
gross value
= impact_score
  * estimated_relative_savings
  * usage_weight
  * regression_weight
```

and discounts it using evidence freshness before dividing by estimated engineering effort. If confidence debt is high, the system returns `remeasure-before-optimization` rather than pretending an old prediction justifies engineering work.

OAK invariant: `roi_proxy` is not realized money, guaranteed savings or proof that an optimization is feasible.

## 11. Multi-language Source Genomes

`omega_compute_physics_t/language_adapters.py`

Python uses AST + Complexity-IR and is marked `syntax-aware`.

R0.6 also recognizes common extensions for C, C++, JavaScript, TypeScript, Rust, Go, Java, C#, Julia, R and shell. These non-Python adapters currently use bounded lexical fingerprints: LOC, function-like blocks, loop tokens, branch tokens, call-like tokens, allocation tokens and brace depth.

They make non-Python code visible immediately, but remain explicitly `heuristic`. Exact parser/compiler/Tree-sitter adapters should replace them where fleet evidence shows sufficient value.

## 12. Universal Fleet Scan

`omega_compute_physics_t/universal_fleet.py`

For every pinned local checkout:

```text
files
-> SHA-256 static snapshot
-> language detection
-> SourceGenome per supported source file
-> Python Complexity-IR
-> Python CallGraph
-> UniversalRepositoryReport
```

Across repositories:

```text
UniversalRepositoryReport[]
-> UniversalFleetReport
```

The report includes source-file counts, language counts, Python IR function counts, call dependencies, unsupported files and parse errors. No repository module is imported or executed.

## 13. Static CLI

R0.6 is installable as:

```bash
omega-compute-r06 snapshot ./repo --repository Tristan-TM-Poly/example --commit <sha>
omega-compute-r06 risk path/to/module.py
omega-compute-r06 call-graph a.py b.py
omega-compute-r06 universal-fleet \
  --repo A=/checkouts/A --commit A=<shaA> \
  --repo B=/checkouts/B --commit B=<shaB>
```

The equivalent module entry point is `python -m omega_compute_physics_t.r06_cli`. All R0.6 CLI operations are static.

## 14. Evidence Schema v0.6

`complexity_atlas/evidence_schema_v0_6.json`

Machine-readable evidence kinds include repository snapshots and diffs, call graphs, fixture registries, risk preflights, benchmark contract plans, regression ledgers, change-impact reports, confidence-debt reports, optimization-ROI proxies, source genomes and universal repository/fleet reports.

Schema validity is not evidence of scientific truth, runtime safety or realized value.

## 15. Fleet-wide operating loop

```text
PIN
-> SNAPSHOT
-> SCAN
-> LINK
-> DIFF
-> PROPAGATE IMPACT
-> RISK
-> PLAN FIXTURE
-> PLAN CONTRACT
-> REVIEW
-> MEASURE EXTERNALLY
-> FIT / VALIDATE
-> DIFF RESOURCES
-> LEDGER
-> COMPUTE CONFIDENCE DEBT
-> RANK REMEASUREMENT
-> RANK OPTIMIZATION ROI
-> REPEAT
```

This is a living computational atlas rather than a collection of isolated benchmark numbers.

## 16. OAK promotion ladder

Static evidence includes changed blobs, SourceGenome/Complexity-IR/call-graph differences, risk indicators and impact propagation. Empirical resource changes require controlled measurements. Mechanistic claims require interventions/counters/independent evidence. Asymptotic mathematical claims require algorithmic or formal proof. No layer is automatically promoted to the next.

## 17. HGFM fleet representation

```text
owner
-> repository
-> commit
-> file
-> language
-> function/structural unit
-> dependency
-> changed region
-> impact cone
-> risk
-> benchmark plan
-> machine
-> resource evidence
-> regression history
-> confidence debt
-> optimization opportunity
```

This hierarchy can become a temporal HGFM where each commit is a new fleet state and measured differences are provenance-preserving edges between states.

## 18. Six-repository rollout

`complexity_atlas/fleet_rollout_manifest_v0_1.json` pins the six currently accessible repositories to exact commit SHAs. Future evidence can therefore be addressed as `repository@commit` rather than a moving branch name.

At R0.6, complete remote-tree ingestion is still a rollout step rather than a claim of completed exhaustive analysis of all repository bytes.

## 19. R0.7 frontier

Highest-value next steps:

1. ingest complete Git trees for every pinned repository into portable Snapshot Ledgers;
2. identify which non-Python languages actually occur and upgrade only valuable adapters to exact parsers;
3. resolve Python imports and qualified call targets across modules/packages;
4. combine snapshot impact, call-graph centrality, empirical regressions and confidence debt into fleet-wide experiment scheduling;
5. synthesize fixture requirements from signatures/type hints without inventing semantics;
6. connect an explicitly authorized execution/sandbox adapter;
7. run Stage B only for deterministic low-risk kernels;
8. store measured cross-commit evidence as temporal HGFM;
9. learn benchmark half-lives per workload family instead of using one configured value;
10. estimate realized optimization value from before/after measurements and compare it with the ROI proxy.

## 20. Hard boundaries

R0.6 does **not** claim complete static call resolution, semantic equivalence across languages, runtime complexity from lexical tokens, security from static risk scanning, executable correctness from fixture metadata, performance regression from changed source alone, realized financial ROI from a planning score, or asymptotic complexity from empirical resource measurements.

These boundaries are architectural invariants, not missing disclaimers.
