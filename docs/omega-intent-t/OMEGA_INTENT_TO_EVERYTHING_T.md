# Ω-INTENT-TO-EVERYTHING-T∞ R0.1

## Intent compiler → evidence graph → orchestration → generators → artifacts → OAK → reports

Ω-INTENT-TO-EVERYTHING-T∞ is a deterministic, OAK-safe compiler that transforms a high-level Tristan intention into a reviewable execution bundle.

```text
human intention
→ normalized machine contract
→ executable documents
→ requirements and claim candidates
→ evidence hypergraph
→ dependency-aware work units
→ generator specifications
→ code/document/test scaffolds
→ streaming logical additions
→ Ω-SANS-PLAFOND GitHub dry-run plan
→ OAK report
→ corrective next intention
```

The system does not treat generated volume as proof of progress. It preserves a continuous relation between intention, requirement, implementation candidate, validation contract, evidence, residual and report.

## Core invariants

1. **Stable identity.** Equivalent normalized intentions receive the same content-derived identifier.
2. **Traceability.** Every requirement originates from an intention and is connected to one or more work units.
3. **Verifiability.** Every requirement and work unit has an explicit acceptance or validation contract.
4. **Acyclic execution.** Work units are scheduled as topological batches; unresolved references or cycles block compilation.
5. **Claim safety.** Generated source is marked as scaffold code and may not be promoted as a completed implementation.
6. **No hidden completion.** Blocked, uncertain and failed objects remain explicit residuals.
7. **No permanent volume ceiling.** Logical capacity is represented by a mixed-radix frontier and streamed in finite slices.
8. **No automatic remote authority.** Compilation and GitHub planning perform zero remote mutations and cannot merge.

## Bundle layout

```text
bundle/
├── intent.json
├── requirements.jsonl
├── claims.jsonl
├── work-units.jsonl
├── generator-specs.jsonl
├── execution-plan.json
├── hypergraph.json
├── hypergraph.graphml
├── artifact-manifest.json
├── additions.jsonl
├── checkpoint.json
├── next-intent.json
├── frontier-manifest.json
├── compilation-result.json
├── documents/
│   ├── intention.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── acceptance_criteria.md
│   └── risk_register.md
├── scaffolds/
├── reports/
│   ├── executive.md
│   └── oak.json
└── github-plan/
```

## Intent contract

```json
{
  "objective": "Develop and compare Tristan fractal transforms",
  "expected_outputs": [
    "theory_documents",
    "mathematical_specifications",
    "code",
    "tests",
    "benchmarks",
    "reports",
    "product_analysis",
    "ip_analysis"
  ],
  "epistemic_constraints": [
    "distinguish_established_results_from_extensions",
    "no_unverified_performance_claims",
    "compare_against_baselines"
  ],
  "completion_conditions": [
    "artifacts_generated",
    "tests_defined",
    "claims_have_evidence_paths",
    "oak_gate_passes"
  ],
  "languages": ["python", "rust", "cpp"],
  "mode": "frontier"
}
```

## CLI

Compile plain text directly:

```bash
omega-intent compile \
  "Develop all Tristan vector-calculus methods and compare them with established baselines" \
  --language python \
  --language rust \
  --language cpp \
  --materialize-scaffolds \
  --github-plan \
  --output-dir generated/omega_intent_t/vector-calculus
```

Compile a JSON contract:

```bash
omega-intent compile intents/transform-lab.json \
  --materialize-scaffolds \
  --github-plan \
  --branch feat/generated-transform-lab \
  --output-dir generated/omega_intent_t/transform-lab
```

Inspect the logical frontier:

```bash
omega-intent frontier
omega-intent frontier --index 123456789
```

Stream 100,000 logical candidates without loading the frontier into memory:

```bash
omega-intent campaign \
  --offset 1000000 \
  --count 100000 \
  --output generated/omega_intent_campaign.jsonl
```

Read a compiled OAK report:

```bash
omega-intent oak generated/omega_intent_t/transform-lab
```

## Logical frontier

The default frontier combines:

- 1,024 domain slots;
- all recognized output families;
- 8 language/backend targets;
- 10 implementation variants;
- 8 validation gates;
- 128 scale profiles.

This creates a very large addressable plan space while retaining constant auxiliary memory for decoding any individual address. The logical frontier is not an executed campaign and does not imply completed code.

`permanent_total_cap = null` means the architecture does not encode a fixed lifetime ceiling. Each concrete run is still finite and bounded by available compute, storage, API quotas, cost, quality, security, IP, rollback and human-authority gates.

## Code that generates code

R0.1 separates five layers:

1. `IntentCompiler` normalizes the intention and emits the evidence bundle.
2. `WorkPlanner` creates verifiable units and their dependency DAG.
3. `MetaGenerator` compiles each work unit into an explicit generator specification.
4. `ScaffoldGenerator` materializes reviewable Python, Rust, C++ or C contracts.
5. `omega_unbounded_t.GitHubDryRunPlanner` shards the addition stream into a reversible GitHub plan.

Generated scaffolds deliberately fail or return an unimplemented status. This prevents code volume from being mistaken for functional completion.

## OAK gate

The built-in gate checks:

- non-empty objective and outputs;
- verifiable requirements;
- requirement-to-work coverage;
- resolved dependencies;
- validation contracts for every work unit;
- valid hypergraph edge references;
- at least one falsification path when tests or benchmarks are requested;
- explicit claim boundaries;
- zero remote mutations and no automatic merge.

A passing gate certifies the compilation pipeline and its traceability invariants only. It does not validate the scientific content proposed by the intention.

## Completion semantics

Absolute completion of an open research universe is not claimed. Completion is relative to an accepted intention contract:

```text
verified accepted requirements
──────────────────────────────
all accepted requirements
```

The final report must distinguish:

- verified;
- generated but untested;
- blocked;
- rejected;
- refuted;
- awaiting human authority;
- deferred by resource pressure.

## GitHub boundary

The `--github-plan` option invokes Ω-SANS-PLAFOND-T∞ in dry-run mode. It produces deterministic shards, tree plans, commit plans, rollback ledgers, checkpoints, hashes, deduplication records and OAK reports. It does not create a branch, commit, push, pull request or merge.

Remote actions remain separately authorized operations.

## OAK status

R0.1 is a research-software prototype. It demonstrates intention normalization, deterministic decomposition, graph construction, dependency scheduling, meta-generation, scaffold generation, streaming frontier campaigns, GitHub dry-run planning and report generation.

It does not claim:

- autonomous completion of arbitrary software or scientific research;
- correctness of generated implementations;
- theorem proving;
- scientific validation;
- patentability;
- product-market fit;
- infinite compute or storage;
- safe autonomous publication or merge.
