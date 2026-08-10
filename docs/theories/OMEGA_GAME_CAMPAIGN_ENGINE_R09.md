# Ω-GAME-SIM-EVO-T∞ R0.9 — Deterministic Campaign Engine

**Status:** executable candidate stacked on R0.8  
**Authority:** benchmark / orchestration / review only

## Goal

Scale finite experimental campaigns over the Cartesian product of agents, layouts and seeds without losing reproducibility or silently redoing completed work.

```text
agents × layouts × seeds × orientations
→ canonical jobs
→ deterministic shards
→ bounded execution slices
→ checkpoint
→ resume / merge
→ deterministic receipts + empirical wall clock
```

## Job identity

One `CampaignJob` specifies exactly:

```text
left agent ID
right agent ID
seed
layout hash or null
orientation
```

Its `job_id` is derived from canonical SHA-256 identity. Population and seed ordering therefore do not change the plan when the normalized experiment is otherwise identical.

## Campaign plan

`plan_campaign`:

1. normalizes/sorts agents;
2. validates unique agent IDs;
3. sorts/validates unique layout hashes;
4. requires unique non-empty seeds;
5. validates every fixed layout against the requested geometric threshold;
6. enumerates pair × seed × orientation × layout jobs;
7. partitions each job by deterministic hash modulo `shard_count`;
8. emits `plan_receipt` over normalized inputs, jobs and shard membership.

The shards must partition all jobs **exactly once**.

```text
SHARDING != PARALLEL_SPEEDUP
```

R0.9 defines a distributable partition. It does not claim that a specific machine, Python runtime or executor will accelerate it.

## Backpressure

`run_campaign_slice(..., max_jobs=N)` executes at most `N` not-yet-completed selected jobs.

This provides a finite backpressure primitive:

```text
large campaign
→ bounded slice
→ checkpoint
→ next bounded slice
```

`max_jobs` is a work admission bound, not a time guarantee.

## Checkpoints

A `CampaignCheckpoint` binds to one exact `plan_receipt` and stores deterministic `CampaignResult` records keyed by `job_id`.

Each result records:

```text
job_id
replay_hash
winner
ticks
event_count
left/right score
layout_hash
result_receipt
```

Resume validates:

- the checkpoint belongs to the same plan;
- every completed job exists in the manifest;
- every result receipt still matches its content.

Completed jobs are skipped rather than rerun.

```text
CHECKPOINT_RESUME != RECOMPUTE
```

## Shard merging

Independent shard checkpoints can be merged when they share the same plan receipt. Duplicate job results are accepted only when their deterministic receipts agree. Conflicting results fail closed.

Thus:

```text
execute shards independently
→ merge checkpoints
→ same deterministic checkpoint receipt as sequential execution
```

for a deterministic engine and identical plan.

## Work units vs wall clock

R0.9 deliberately stores two classes of measurement.

### Deterministic work accounting

```text
match_ticks_work_units = Σ match.ticks
event_work_units       = Σ replay event count
```

For a deterministic campaign these should reproduce exactly.

### Empirical hardware/runtime observation

```text
wall_clock_seconds
observed_matches_per_second
```

These depend on machine load, runtime, cache, interpreter, thermal state and other external factors.

The wall-clock values are **excluded from deterministic receipts**.

```text
WORK_UNITS != WALL_CLOCK
SHARD_COUNT != SPEEDUP
OBSERVED_THROUGHPUT != UNIVERSAL_PERFORMANCE
```

## Benchmark

`benchmark_campaign` repeats the same full manifest and requires every deterministic checkpoint receipt to agree. It reports deterministic tick/event totals and empirical per-run wall-clock observations.

The benchmark receipt hashes deterministic experiment identity/results, not wall time.

This prevents a noisy timing fluctuation from changing experimental provenance.

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/campaign_engine_demo.py
```

The demo:

1. compiles the fixed-layout GameSpec;
2. creates a four-agent mirrored campaign;
3. partitions it into four shards;
4. runs it through `max_jobs=5` backpressure slices;
5. independently executes each shard;
6. merges shard checkpoints;
7. verifies sequential-resume and shard-merge receipts agree;
8. runs a two-repetition empirical benchmark.

## OAK boundaries

```text
SHARDING != SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
OBSERVED_WALL_CLOCK != DETERMINISTIC_PROVENANCE
CHECKPOINT_RECEIPT != EXTERNAL_CERTIFICATION
CAMPAIGN_COMPLETION != SCIENTIFIC_TRUTH
HIGH_THROUGHPUT != HIGH_QUALITY_EXPERIMENT
```

## Next

R0.10 should add persistence adapters for checkpoint files/artifacts, shard assignment manifests, retry/lease semantics and failure receipts, followed by process-level parallel experiments whose speedup is measured against the same campaign baseline rather than assumed.
