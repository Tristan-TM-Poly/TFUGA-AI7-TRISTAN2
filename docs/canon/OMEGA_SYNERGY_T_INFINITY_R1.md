# Ω-SYNERGY-T∞ — Synergy Foundry R1

**Status:** executable research architecture, review-only by default.  
**Primary claim:** the repository can compile documented creations into typed capabilities, needs, interfaces, candidate synergies, causal experiments, PR plans and evidence ledgers without treating heuristic discovery as proof.

## Epistemic ladder

```text
connection -> hypothesis
interface -> integration design
prototype -> executable composition
gain -> measured observation
causal gain -> ablation/control evidence
robust gain -> independent replication
reuse -> canonical capability
```

A high score never skips this ladder.

## Central loop

```text
repositories + theory + tests + schemas + reports
  -> CreationDNA
  -> CreationGraph
  -> capability/need closure
  -> SynergyTensor
  -> bounded n-order search
  -> portfolio selection
  -> experiment + counterfactual twin
  -> PR Genome + PR Orchestra
  -> OAK proof ledger
  -> meta-synergy
  -> product hypothesis
```

## CreationDNA

Every discovered system receives a machine-readable record:

- accepted and produced artifact types;
- explicit transformations extracted from `X -> Y` statements;
- documented needs and TODO gates;
- domains, tokens and source paths;
- evidence records and provenance;
- risks, permissions, uncertainty and maturity;
- expansion options such as adapter, benchmark, experiment or product hypothesis.

Extraction is conservative. Missing documentation can lower a system's rank even when its code is strong; this is emitted as an uncertainty rather than silently repaired.

## SynergyTensor

A candidate is evaluated on positive and negative axes.

### Positive axes

- semantic resonance;
- capability–need complementarity;
- interface compatibility;
- closure gain;
- evidence strength;
- causal readiness;
- reuse;
- option value;
- product value.

### Negative axes

- operational, legal, safety and epistemic risk;
- integration cost;
- uncertainty;
- coupling and debt.

The tensor remains visible in full. A scalar total exists only to schedule finite experiments.

## Closure Engine

The engine searches for a minimal falsifiable bridge when a provider produces an artifact type needed by a target. Every bridge includes:

- provider, target, capability and need identifiers;
- source and target artifact types;
- an interface mapping;
- preserved invariants;
- declared losses;
- round-trip, schema and provenance tests;
- expected gain and a falsification test.

A bridge with undeclared losses is invalid.

## Anti-synergies

The first-class negative registry includes:

- lexical similarity without capability–need closure;
- duplicated capabilities;
- missing interface;
- weak evidence;
- high risk;
- negligible expected gain;
- large order with rising integration debt.

Failed combinations should be archived in M⁻ with context and possible rehabilitation conditions.

## Bounded n-order search

Complete enumeration is combinatorial. The implementation therefore:

1. builds token and domain buckets;
2. evaluates candidate pairs;
3. retains a finite beam;
4. extends only promising neighborhoods;
5. penalizes higher order and weak bottlenecks;
6. reports all limits.

Beam search can miss fertile combinations. That limitation is part of the output.

## Causal Experiment Compiler

Every candidate receives:

- isolated-component baselines;
- a simplest external baseline;
- interface and routing ablations;
- negative controls;
- deterministic seeds and frozen data;
- perturbation tests;
- preregistered metrics;
- success, failure and stopping criteria;
- rollback recipes;
- expected evidence artifacts.

The counterfactual twin asks whether a simpler system or placebo adapter could produce the same observation.

## Synergy Proof Ledger

The proof ledger is append-only JSONL with a SHA-256 hash chain. Entries retain:

- synergy and event identifiers;
- claim text;
- measurements;
- evidence hashes;
- limitations;
- authority level;
- previous and current entry hashes.

Hash-chain integrity proves only ledger consistency, not scientific truth.

## Half-life

Confidence decays after validation:

```text
C(t) = C0 * 2^(-t / half_life)
```

Volatile dependencies, APIs, datasets and regulated domains should use shorter half-lives. Revalidation does not occur automatically through self-assertion; it requires a new evidence event.

## PR Genome and PR Orchestra

An experiment compiles into a PRGene with:

- intention and candidate identifier;
- affected paths;
- capabilities added and needs resolved;
- interfaces provided and consumed;
- tests and gates;
- risk tensor;
- dependencies and conflicts;
- rollback;
- option value.

PR Orchestra topologically schedules independent waves and never places known conflicts in the same wave. The manifest explicitly authorizes no merge.

## Meta-Synergy Reactor

Candidate pipelines can be composed when output and input types are compatible. A meta-synergy reports:

- ordered primitive candidates;
- composition edges and compatibility;
- conserved invariants;
- propagated losses;
- propagated uncertainty;
- estimated value;
- reversibility.

Higher order is useful only when the complete pipeline beats a simpler baseline.

## Product compiler

A technical candidate becomes only a product hypothesis. It must still establish:

- a real user and problem;
- a measurable reduction in time, error, cost or risk;
- a technical baseline;
- license, privacy and security review;
- repeated use or payment.

The first strategic offer remains a service-led repository audit combining OAKGate, documentation consistency and PR risk analysis.

## Outputs

```text
creation_dna.json
system_inventory.json
creation_graph.json
creation_graph.dot
synergy_report.json
synergy_n.json
experiment_queue.json
research_queue.json
counterfactual_twins.json
closure_bridges.json
portfolio.json
pr_orchestra.json
meta_synergies.json
product_hypotheses.json
SYNERGY_FOUNDRY_REPORT.md
```

Compatibility aliases preserve the original Ω-SYNERGY-N-T workflow while the new Foundry schema is version `1.0`.

## Autonomy boundary

Allowed automatically in this implementation:

- read repository files;
- calculate review-only scores;
- generate local reports and experiment plans;
- upload CI artifacts.

Not authorized automatically:

- merging PRs;
- publishing scientific, legal, safety, patent or revenue claims;
- spending money;
- contacting users or institutions;
- exposing private intellectual property;
- deploying physical or regulated systems.

## Canonical commands

```bash
python -m omega_synergy_t \
  --repo-root . \
  --max-order 4 \
  --beam-width 96 \
  --top-k 25

python tools/github_reactor/synergy_n_engine.py \
  --repo-root . \
  --out reports/github-autonomous-reactor/synergy-foundry
```

## OAK commandments

1. Connect transformations, not merely names.
2. Close loops instead of multiplying concepts.
3. Measure gain rather than generated line count.
4. Preserve evidence domains and provenance.
5. Declare interface losses.
6. Compare every complex composition to a simple baseline.
7. Keep remote mutation, publication and merge behind explicit authority.
8. Convert every useful failure into M⁻.
9. Revalidate confidence after its half-life.
10. Treat a product as real only after external use and value evidence.

## R1 foundation tests

The executable foundation is designed to prove that:

- capability–need matching can succeed without exact system-name identity;
- lexical similarity without closure is flagged as a false-synergy risk;
- bounded search is deterministic;
- every experiment includes baselines, ablations, OAK gates and rollback;
- ledger tampering is detected;
- confidence decays under a declared half-life;
- PR orchestration never grants merge authority;
- Shapley-style credit sums to coalition value for additive test cases;
- the complete bundle remains review-only.

## Strategic crystallization

The first real constellation remains:

```text
Ω-DOC-T × OAKGate × PR Genome
  -> detect code/documentation divergence
  -> produce a reproducer and baseline
  -> generate a review-only corrective PR gene
  -> measure reduced error and review time
  -> compile a paid repository-audit hypothesis only after evidence
```

The purpose of Ω-SYNERGY-T∞ is not to generate the largest possible number of combinations. It is to increase the number of closed, measured, reusable and governed transformations per unit of time, risk and integration debt.
