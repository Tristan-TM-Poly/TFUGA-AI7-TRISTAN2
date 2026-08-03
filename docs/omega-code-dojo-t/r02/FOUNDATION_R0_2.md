# Ω-CODE-DOJO-T∞ R0.2

## Status

R0.2 is an OAK-safe software-research foundation for extensible algorithmic training campaigns. It does not claim neural-model training, affiliation with Codewars, general solver optimality, scientific validation, security certification, or formal proof of arbitrary generated programs.

## Core distinction

The system separates:

1. source code;
2. logical address space;
3. materialized cells;
4. executed experiments;
5. supported software fixtures;
6. externally validated claims.

The default logical frontier contains exactly **3,221,225,472** addresses:

- 128 domains;
- 64 archetypes;
- 32 difficulty bands;
- 24 language targets;
- 16 execution regimes;
- 32 mutation families.

The frontier is addressed arithmetically. It is not materialized as billions of files.

## No permanent cap

Every campaign is finite because execution must be accountable. A campaign has a local materialization budget, resource accounting and stop conditions. By default, `permanent_total_cap` is `null`: the next campaign may extend the frontier, resume from another shard or add new axes.

```text
finite campaign != permanent system ceiling
```

## Modules

- `models.py`: TaskIR, provenance, frontier cells, skill posteriors, observations and receipts.
- `frontier.py`: mixed-radix addressing and extensible axes.
- `task_ir.py`: deterministic TaskIR v2 compiler.
- `provenance.py`: conservative IPGate.
- `curriculum.py`: Beta-posterior skill graph and active utility ranking.
- `generators.py`: task-generator plugin protocol.
- `mutation.py`: mutation registry and deterministic research fixtures.
- `campaign.py`: adaptive finite campaigns over the logical frontier.
- `memory.py`: M⁻ failure genomes and M⁺ strategy genomes.
- `oracles.py`: exact and property OracleMesh.
- `scheduler.py`: deterministic resumable shards.
- `dataset.py`: SFT, preference, critique, proof and translation manifests.
- `receipts.py`: canonical SHA-256 signing and tamper verification.

## Campaign loop

```text
logical frontier
  -> candidate ordinal sampling
  -> active curriculum ranking
  -> IPGate
  -> TaskIR generation
  -> validation
  -> mutation fixture
  -> M+/M- compatible observation
  -> skill posterior update
  -> canonical receipt
```

## OAK boundary

`CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2` means only that the deterministic software invariants encoded by the benchmark passed. It is not evidence that generated tasks are pedagogically optimal, that generated algorithms are correct, or that a neural model was trained.

## Commands

```bash
omega-code-dojo-r02 frontier --sample 8
omega-code-dojo-r02 campaign --budget 64
omega-code-dojo-r02 campaign --budget 64 --permanent-cap 32
omega-code-dojo-r02 benchmark --budget 32
```

## Validation target

The CI checks Python 3.10 through 3.13, byte-for-byte deterministic benchmark output, TaskIR and receipt schemas, the 3,221,225,472-cell frontier, no permanent cap by default, provenance blocking, receipt tamper detection, memory, scheduler, dataset and OracleMesh behavior.

## Next gate

R0.3 should replace deterministic mutation fixtures with actual subprocess-isolated language runners, resource limits, differential testing and shrinking of minimal counterexamples. Until then, mutation results remain software fixtures and must not be reported as measurements of arbitrary external code.
