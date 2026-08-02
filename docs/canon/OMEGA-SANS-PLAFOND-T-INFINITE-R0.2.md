# Ω-SANS-PLAFOND-T∞ R0.2

## Streaming GitHub Dry-Run Planner

Status: **coded planning prototype / local filesystem writes only / zero remote GitHub mutations**.

R0.2 extends the R0.1 adaptive frontier controller with a streaming compiler for tens of thousands or more logical additions:

```text
JSONL addition stream
→ normalize
→ deterministic identity
→ disk-backed deduplication
→ adaptive semantic shards
→ atomic finalize + SHA-256
→ Git tree ledger
→ commit plan
→ rollback plan
→ semantic diff
→ OAK report
→ explicit human authorization gate
```

## What “no maximum” means

The planner does not expose a total-record parameter such as:

```python
MAX_ADDITIONS = 1200
```

It consumes an iterable until that iterable is exhausted or a real error occurs. A finite command may deliberately generate 100,000 records for a stress experiment, but `100000` is the experiment workload, not the planner’s permanent capacity ceiling.

The planner remains constrained by reality:

- disk space and filesystem behavior;
- CPU, RAM, I/O and elapsed time;
- data validity and provenance;
- Git object behavior;
- CI duration and cost;
- GitHub/API quotas and terms;
- IP, legal, security and publication gates.

Every such constraint is an observable frontier, not permission to bypass safeguards.

## Logical additions are not Git objects

One logical addition can be a claim, citation, test, invariant, relation, counterexample, code fragment, measurement or M⁻ event. R0.2 groups many logical additions into hashed JSONL shards.

```text
40,000 logical additions
≠ 40,000 files
≠ 40,000 commits
≠ 40,000 API calls
```

The unit pipeline is:

```text
micro-addition → semantic stream → adaptive shard → planned Git path → commit group
```

## Addition record

```json
{
  "addition_id": "claim-000001",
  "namespace": "spectroscopy",
  "kind": "claim",
  "payload": {
    "statement": "Example claim candidate"
  },
  "provenance": [
    "source://example/1"
  ],
  "risk": "normal",
  "metadata": {
    "oak_status": "candidate"
  }
}
```

`addition_id` may be omitted. A deterministic identifier is then derived from the normalized semantic identity.

## Disk-backed identity

Exact semantic identities are stored in SQLite instead of a process-wide Python set. The fingerprint is derived from:

```text
namespace + kind + payload + provenance
```

This design keeps uniqueness state outside RAM and allows future resume, partitioning and distributed index adapters.

A repeated fingerprint is written to `duplicates.jsonl` and not integrated twice. Independent provenance remains distinguishable because provenance participates in the identity.

## Adaptive shards

Each `(namespace, kind)` stream owns a shard writer. `initial_shard_bytes` is a starting calibration, not a total ceiling. After each successful atomic finalization:

\[
S_{n+1}=\max(S_n+1,\lfloor gS_n\rfloor),\quad g>1
\]

The next shard can therefore test a larger byte frontier. When that frontier fails in later versions, the failure must become an M⁻ event and trigger a redesigned storage strategy rather than a permanent global record limit.

Each shard stores:

- namespace and kind;
- sequence number;
- logical addition count;
- byte count;
- SHA-256;
- byte budget used;
- human-approval requirement.

## Atomic finalization

A shard is written under `.staging/`, flushed, synchronized, closed, then moved atomically to its final path. The tree ledger is updated only after finalization.

```text
write temporary
→ flush
→ fsync
→ close
→ atomic replace
→ index shard
→ append tree ledger
→ append rollback recipe
→ checkpoint
```

## Human sovereignty

Risk labels such as these route the containing shard to explicit review:

- `ip_sensitive`;
- `public`;
- `irreversible`;
- `legal`;
- `financial`.

R0.2 does not create a branch, stage files, commit, push, open a PR, publish, delete, change permissions or spend money.

The generated `commit-plan.jsonl` contains suggested commands such as:

```text
git add -- shards/spectroscopy/claim/shard-00000001.jsonl
```

These are plans, not executed commands.

## Invalid records and M⁻

Invalid records are quarantined instead of silently dropped:

```text
quarantine.jsonl
m_minus.jsonl
```

Strict mode can fail immediately. Default mode continues processing valid records while preserving every rejected record and diagnostic.

A provenance-required policy can convert missing provenance into a quarantined M⁻ event.

## Outputs

```text
generated/omega_unbounded_github_plan/
├── .staging/
├── shards/
├── plan-index.sqlite3
├── tree.jsonl
├── commit-plan.jsonl
├── rollback.jsonl
├── duplicates.jsonl          # when duplicates exist
├── quarantine.jsonl          # when invalid records exist
├── m_minus.jsonl             # when invalid records exist
├── checkpoint.json
├── manifest.json
├── semantic-diff.json
└── oak-report.json
```

## CLI

Compile an existing stream:

```bash
omega-unbounded plan additions.jsonl \
  --output-dir generated/omega_unbounded_github_plan \
  --initial-shard-bytes 262144 \
  --shard-growth-factor 2 \
  --require-provenance \
  --branch feat/generated-canon
```

Stress the planner without materializing an input file:

```bash
omega-unbounded synthetic-plan \
  --work-items 100000 \
  --namespaces 8 \
  --output-dir generated/frontier-100k
```

Again, `--work-items` defines this finite experiment. It does not impose a planner maximum.

## R0.2 OAK invariants

A successful dry-run asserts:

1. no total addition cap exists in the planner policy;
2. uniqueness is disk-backed;
3. shard finalization is atomic;
4. every planned shard has a content hash;
5. every generated shard has a rollback recipe;
6. sensitive risks are routed to approval;
7. invalid records are quarantined or fail closed;
8. remote mutation count is exactly zero;
9. scientific validity is not inferred from successful integration;
10. physical and provider constraints remain explicit.

## Tests

```bash
python -m pytest \
  tests/test_omega_unbounded_t.py \
  tests/test_omega_unbounded_github_planner.py
```

The planner test integrates 40,000 synthetic logical additions, verifies every shard hash, validates the commit and rollback ledgers, confirms adaptive shard growth and checks that no total-cap field appears in the result model.

## Next frontier — R0.3

R0.3 should add:

1. resume from a partial checkpoint;
2. dependency-aware topological shard ordering;
3. external resource telemetry and backpressure;
4. M⁺ breakthrough records paired with M⁻;
5. differential test routing by changed namespace;
6. Git object-size and packfile frontier experiments;
7. content-addressed object-store adapters;
8. multi-process and distributed partition ownership;
9. a GitHub actuator that remains dry-run-first and phase-authorized;
10. reproducible comparison of architectures by throughput, cost, quality and rollback fidelity.

## Canonical rule

> The system does not replace one arbitrary ceiling with a larger arbitrary ceiling. It streams until the workload or a real frontier ends the run, preserves every failure, redesigns the architecture, and repeats at a larger verified scale.
