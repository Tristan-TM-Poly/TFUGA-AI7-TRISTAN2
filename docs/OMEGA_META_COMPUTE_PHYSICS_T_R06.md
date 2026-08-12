# Ω-META-COMPUTE-PHYSICS-T∞ — R0.6 Universal Fleet Intelligence

Status: **D-MVP candidate / R0.6**. Commit-addressed, static-first fleet intelligence with evidence-aware revalidation and optimization planning. No arbitrary target-code execution.

## Mother pipeline

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

## Snapshot Ledger

`omega_compute_physics_t/snapshot_ledger.py` records repository identity, pinned commit SHA, file path, byte size, content identity, extension counts and total bytes. Git-tree records can retain Git blob identities; local read-only checkouts use SHA-256. `compare_snapshots` classifies added, removed, changed and unchanged files.

```text
changed blob != semantic regression != performance regression
```

## Complexity-IR and Call Graph

`complexity_ir.py` converts Python syntax into a hardware-independent inventory (`LOAD`, `STORE`, `ARITH`, `COMPARE`, `INDEX`, `CALL`, `LOOP`, `BRANCH`, `ALLOC`, `COMPREHENSION`, `AWAIT`, `YIELD`). `call_graph.py` adds resolved/unresolved calls, fan-in/fan-out, strongly connected components and recursive components.

The graph is conservative: dynamic dispatch, reflection, imports, monkey patching and decorators can make runtime behavior different.

## Change-Impact Propagation

`change_impact.py` propagates a `SnapshotDiff` through the reverse static call graph. Directly changed modules get distance 0; callers receive decaying bounded impact. Changed files absent from the graph stay explicit as unresolved impact.

```text
static impact score != semantic impact != measured performance impact
```

## Fixture Registry and Contract Planner

`fixture_registry.py` records deterministic, pure-data input metadata and rejects network-backed/nondeterministic automatic fixtures. `contract_planner.py` binds a Stage A benchmark seed, pinned commit, fixture, explicit axis values and static risk evidence into a `BenchmarkContract` candidate.

Generated contracts deliberately remain `trusted_checkout=False`: contract generation is planning, not authorization.

## Static Risk Preflight

`risk_preflight.py` over-approximates indicators of network access, credentials/secrets, mutating filesystem operations, subprocess/external effects and privileged operations, retaining line-located evidence.

```text
no static risk flag != safe code
```

A clean report is never a sandbox certification.

## Regression Ledger

`regression_ledger.py` converts finite-domain `ComplexityDiffReport` evidence into commit-addressed regression events with severity and rebenchmark decisions.

```text
finite-domain resource regression != asymptotic complexity-class regression
```

## Confidence Debt

`confidence_debt.py` models evidence freshness with configurable half-life:

```text
freshness = 2^(-age_days / half_life_days)
```

Debt combines staleness, calibration gap, certified-domain mismatch, code change and machine change. It routes evidence into `fresh-enough`, `schedule-revalidation`, `high-revalidate` or `critical-revalidate`.

Confidence debt is a scheduling heuristic, not a posterior probability of falsehood.

## Evidence-aware Optimization ROI

`optimization_roi.py` separates optimization priority from measurement priority. Its dimensionless gross-value proxy is:

```text
impact_score
* estimated_relative_savings
* usage_weight
* regression_weight
```

The score is discounted by evidence debt and divided by estimated engineering effort. High debt produces `remeasure-before-optimization`.

The ROI proxy is not realized money, guaranteed savings or proof that an optimization is feasible.

## Multi-language Source Genomes

`language_adapters.py` uses AST + Complexity-IR for Python (`syntax-aware`). It recognizes C, C++, JavaScript, TypeScript, Rust, Go, Java, C#, Julia, R and shell using bounded lexical fingerprints so non-Python code becomes visible immediately. Those adapters remain explicitly `heuristic`; exact parsers should replace them selectively when evidence shows value.

## Universal Fleet Scan

`universal_fleet.py` statically combines, per pinned checkout:

```text
files
-> SHA-256 snapshot
-> language detection
-> SourceGenome
-> Python Complexity-IR
-> Python CallGraph
-> UniversalRepositoryReport
```

Multiple reports become `UniversalFleetReport` with language counts, source counts, Python IR functions, dependencies, unsupported files and parse errors. No target module is imported or executed.

## CLI

R0.6 is installable as `omega-compute-r06`:

```bash
omega-compute-r06 snapshot ./repo --repository Tristan-TM-Poly/example --commit <sha>
omega-compute-r06 risk path/to/module.py
omega-compute-r06 call-graph a.py b.py
omega-compute-r06 universal-fleet \
  --repo A=/checkouts/A --commit A=<shaA> \
  --repo B=/checkouts/B --commit B=<shaB>
```

Equivalent module entry point: `python -m omega_compute_physics_t.r06_cli`. All R0.6 CLI operations are static.

## Evidence Schema

`complexity_atlas/evidence_schema_v0_6.json` supports repository snapshots/diffs, call graphs, fixture registries, risk preflights, benchmark contract plans, regression ledgers, change-impact reports, confidence-debt reports, optimization-ROI proxies, source genomes and universal repository/fleet reports.

Schema validity is not scientific truth, runtime safety or realized value.

## Fleet-wide loop

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
-> CONFIDENCE DEBT
-> RANK REMEASUREMENT
-> RANK OPTIMIZATION ROI
-> REPEAT
```

## OAK promotion ladder

Static evidence includes changed blobs, source/IR/call-graph differences, risk indicators and impact propagation. Empirical resource changes require controlled measurements. Mechanistic claims require interventions/counters/independent evidence. Asymptotic claims require algorithmic or formal proof. No layer promotes itself automatically.

## HGFM fleet representation

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

This can become a temporal HGFM: commits are fleet states and validated differences are provenance-preserving edges.

## Six-repository rollout

`complexity_atlas/fleet_rollout_manifest_v0_1.json` pins the six currently accessible repositories to exact commit SHAs. Evidence can therefore be addressed as `repository@commit`, not a moving branch. Complete remote-tree ingestion remains a rollout step; R0.6 does not claim exhaustive analysis of every repository byte yet.

## R0.7 frontier

1. ingest complete pinned Git trees for every fleet repository;
2. inventory actual language distribution and upgrade only valuable lexical adapters to exact parsers;
3. resolve qualified Python imports/calls across packages;
4. unify snapshot impact, call-graph centrality, empirical regressions and confidence debt into experiment scheduling;
5. infer fixture requirements from type/signature evidence without inventing semantics;
6. connect an explicitly authorized execution/sandbox adapter;
7. run Stage B only for deterministic low-risk kernels;
8. store cross-commit measured evidence as temporal HGFM;
9. learn benchmark half-lives per workload family;
10. compare predicted Optimization ROI against measured before/after savings.

## Hard boundaries

R0.6 does **not** claim complete call resolution, semantic equivalence across languages, runtime complexity from lexical tokens, security from static risk scans, executable correctness from fixture metadata, performance regression from changed source alone, realized financial ROI from planning scores, or asymptotic complexity from empirical measurements.

These boundaries are architectural invariants.
