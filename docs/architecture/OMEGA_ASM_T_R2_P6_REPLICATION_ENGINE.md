# Ω-ASM-T∞ R2 — P6 Replication Engine

**Status:** stacked implementation on top of the P5 foundation PR.  
**Authority:** `review_only`.  
**Important:** this engine can classify replicated evidence; its existence does not mean a real P6 campaign has already been completed.

## Purpose

P5 characterizes one execution context. P6 asks whether multiple P5 observations describe the **same identified target and the same measured binary** strongly enough to support a target-specific replicated claim.

```text
P5 report 1 ┐
P5 report 2 ├─> identity + binary equivalence -> group -> distributions -> P6 status
P5 report N ┘
```

The core rule is:

```text
ReplicationKey = SHA256(MachineFingerprint || BinarySHA256)
```

A report can contribute to the replication threshold only when:

1. it is a structurally acceptable P5 report;
2. `availability == available`;
3. the machine identity is informative;
4. the measured binary has a valid SHA-256;
5. its machine fingerprint matches the group;
6. its binary SHA-256 matches the group.

## Stable machine identity

`canonical_machine_identity()` intentionally separates **identity** from **conditions**.

Identity currently includes:

```text
architecture
vendor
family
model
stepping
model_name
hash(sorted ISA feature mask)
cache geometry:
  level
  type
  size
  line size
  associativity
  sets
```

Not used as identity:

```text
current frequency
frequency governor
runner name
OS patch level
toolchain version
```

Those values can still matter to performance and remain in the original P5 provenance, but changing them does not by itself claim that a different processor model is present.

This choice is deliberately conservative in the other direction for ISA features: if virtualization masks or exposes different ISA features, the target fingerprint changes because executable compatibility and optimization choices can change.

## Binary identity

P6 never merges measurements of different binaries merely because they came from the same source file or compiler command.

The measured binary must expose:

```text
binary.exists = true
binary.sha256 = 64 hex characters
```

Different hashes create different replication groups.

Future work may add a source/disassembly/toolchain equivalence graph, but that will not weaken the binary-identity rule for raw benchmark replication.

## Replication threshold

Default:

```text
minimum_available_replicates = 3
```

The threshold is configurable but cannot be lower than 2.

Only `available` P5 reports count toward it.

```text
partial      -> retained as provenance, count = 0 toward threshold
unavailable  -> retained as provenance, count = 0 toward threshold
malformed    -> excluded with explicit reasons
```

## Campaign statuses

### `replicated_identified_target`
Exactly one machine+binary group exists and it reaches the available-report threshold.

### `replicated_target_with_additional_groups`
One group reaches the threshold, while other target/binary groups are also present but do not all qualify.

### `multiple_replicated_targets`
More than one distinct machine+binary group independently reaches the threshold.

### `mixed_or_insufficient_targets`
Multiple groups exist but none reaches the threshold.

### `insufficient_replication`
No group reaches the threshold and there is at most one eligible group.

No status authorizes a universal performance claim.

## Metric distributions

For each qualifying or non-qualifying group, the engine summarizes available non-negative finite P5 derived metrics:

```text
ipc
cycles_per_instruction
branch_miss_rate
cache_miss_rate
```

Each metric keeps the R1 robust distribution contract:

```text
count
minimum
median
mean
maximum
stdev
MAD
p05
p95
```

A distribution is evidence, not a proof that the system is stationary or normally distributed.

## CLI

```bash
omega-asm p6-aggregate run1.json run2.json run3.json
omega-asm p6-aggregate run*.json --min-replicates 5 --output campaign.json
```

The input files are P5 report JSON objects.

## OAK exclusions

Malformed inputs are not silently repaired into P6 evidence. They are listed in:

```text
excluded_reports:
  - index
  - reasons[]
```

Typical reasons:

- wrong evidence level;
- invalid availability;
- missing `review_only` authority;
- missing machine manifest;
- available P5 evidence without binary SHA-256;
- machine identity too weak to identify a target.

## Promotion contract

A P6 campaign report records:

```text
same_machine_fingerprint_required = true
same_binary_sha256_required = true
available_p5_reports_required = N
partial_or_unavailable_reports_count_toward_threshold = false
universal_claim_allowed = false
automatic_authority_promotion = false
```

This means a tool cannot legitimately reinterpret the JSON later as a universal benchmark claim without violating the report's own contract.

## What P6 still needs experimentally

The replication engine is infrastructure. A strong real campaign should additionally control or record, where possible:

- workload/data identity;
- compiler and linker commands;
- binary/disassembly hashes;
- CPU affinity;
- frequency/turbo/governor behavior;
- thermal state;
- virtualization;
- background load;
- repeated timing distributions;
- hardware-counter running percentage/multiplexing;
- independent reruns across sessions/machines.

## M− / anti-claims

- Three reports copied from the same underlying measurement are not three independent replications.
- Same CPU model does not guarantee identical thermal/frequency conditions.
- Same source does not guarantee same binary.
- Same binary on a different ISA-feature mask is not the same conservative target fingerprint.
- Median IPC is not application-level speedup.
- P6 target-specific evidence is not a universal x86-vs-ARM or C-vs-Rust conclusion.
- P6 does not prove semantic equivalence; P7 remains separate.

## Next step

After P5/P6 infrastructure is green, the highest-value next branch is a controlled **compiler parallax campaign**:

```text
same semantic fixture
-> C / C++ / Rust / ASM
-> exact compiler flags
-> binary + disassembly hashes
-> P3 correctness
-> P4 timing
-> P5 counters
-> P6 grouped replication
```

Only after that should calibrated target-specific cost models or superoptimizer ranking learn from the measurements.
