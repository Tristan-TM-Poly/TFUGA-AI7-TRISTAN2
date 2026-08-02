# Ω-MAIL-T R0.2 Massive

## 49,152 deterministic, linked, synthetic test records

Ω-MAIL-T R0.2 expands the R0.1 executable mail sandbox into a sharded intercompany scenario and benchmark atlas.

The checked-in release materializes:

- **16,384 scenario templates**;
- **32,768 linked benchmark templates**;
- **49,152 total records**;
- 16 synthetic Tristan companies;
- 16 business intents;
- 16 anomaly families;
- four locale variants;
- two benchmarks for every scenario;
- eight scenario shards and eight benchmark shards;
- deterministic IDs and SHA-256 fingerprints;
- streaming queries, audit CLI, scale tests, and OAK boundaries.

## Exact cardinality

```text
16 companies × 16 intents × 16 anomaly families × 4 locales
= 16,384 scenario templates
```

Every scenario has two explicit benchmark templates:

```text
16,384 scenarios × 2 benchmarks
= 32,768 benchmark templates
```

The combined versioned corpus contains:

```text
16,384 + 32,768 = 49,152 records
```

This finite checked-in release is a reproducible frontier, not a permanent maximum. Shard count is only a storage-layout parameter.

## Companies

The first atlas models synthetic identities for Tristan OAK Systems, Tristan Software Labs, Tristan Research Foundry, Tristan Spectroscopy, Tristan Materials, Tristan Energy Systems, Tristan Quantum Labs, Tristan Crystal Systems, Tristan Mail Systems, Tristan Audit Services, Tristan Legal & IP, Tristan Finance, Tristan Security, Tristan Education, Tristan Game Worlds, and Tristan Holding.

Every generated address uses the reserved `.test` suffix and every scenario declares `external_delivery_allowed=false`.

## Business intents

The first 16 intent families cover support, billing, security, research, publication approval, software patches, procurement, contracts, meetings, data access, incident escalation, quality audits, experiment handoffs, customer feedback, compliance questions, and executive decisions.

Each intent maps to:

- an expected semantic classification;
- a sender role;
- a recipient role;
- an expected organizational route;
- an explicit negative control.

## Anomaly families

The 16 anomaly families include the nominal case plus missing subjects, missing or duplicate attachments, contradictory identifiers, wrong language, unknown aliases, delayed or duplicate delivery, out-of-order replies, oversized attachments, HTML/plain-text mismatch, synthetic secret markers, permission boundaries, ambiguous urgency, and thread-reference gaps.

The anomaly field specifies what the future executable conversation simulator must inject. A template is not evidence that the fault has already been implemented or detected.

## Benchmark pair

Every scenario receives a semantic-routing benchmark and an OAK-safety benchmark.

The routing benchmark checks the expected classification and target organizational role against an unrelated-department negative control. The safety benchmark checks that external delivery remains disabled and that unsafe permission or delivery transitions are rejected.

These are test specifications. They become executed evidence only when a runner produces a result and the result is preserved with provenance.

## Generate and verify

```bash
python tools/generate_omega_mail_r02_massive.py --root .
python -m omega_mail_t.catalog_cli stats
python -m omega_mail_t.catalog_cli audit
python -m omega_mail_t.catalog_cli query \
  --company tristan_oak_systems \
  --intent security_alert \
  --anomaly permission_boundary \
  --locale fr-CA \
  --limit 8
```

Installed entry point:

```bash
omega-mail-catalog audit
```

## Repository outputs

```text
generated/omega_mail_t_r02/
├── manifest.json
├── OAK_STATUS.md
├── scenarios/
│   ├── scenarios-000.jsonl
│   └── ...
└── benchmarks/
    ├── benchmarks-000.jsonl
    └── ...
```

The JSONL layout supports streaming, sharded validation, incremental diffs, cold-storage migration, checkpointing, and future graph indexing.

## Determinism

The generator emits stable JSON with sorted keys, deterministic IDs, and combined scenario and benchmark fingerprints. GitHub Actions regenerates the atlas twice and compares manifest hashes before committing generated outputs.

## OAK boundary

```text
scenario template != delivered email
benchmark template != executed test
synthetic identity != legal person
.test address != consent
large atlas != high test quality
passing synthetic test != production readiness
classification match != correct business decision
generated conversation != customer evidence
```

The atlas contains no real recipients, private customer data, authentic credentials, production-domain permission, or authorization to send external mail.

## Unbounded iteration architecture

R0.2 avoids a permanent `MAX_SCENARIOS` constant. Expansion proceeds by:

- adding semantic companies, roles, intents, locales, channels, and anomalies;
- loading future axes from versioned data files;
- adaptive sharding based on measured file and CI limits;
- streaming rather than materializing all records in memory;
- checkpoints and restartable generation;
- hashes, provenance, negative memory, and rollback plans;
- full validation of high-risk records and sampled validation of safe bulk;
- moving cold shards outside Git history when repository cost becomes harmful.

The objective is not arbitrary line count. The objective is a navigable, reproducible, falsifiable search space whose records can be promoted into executed conversations and regression evidence.

## Next release

R0.3 should convert the templates into executable multi-turn conversations with simulated latency, bounce, duplication, reordering, quarantine, agent replies, workflow creation, causal traces, and M⁻ regression generation.
