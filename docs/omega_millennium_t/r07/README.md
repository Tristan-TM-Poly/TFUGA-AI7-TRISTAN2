# Ω-PROBLEM-ATLAS-T∞ R0.7 — Certified Offline Job Runners

R0.7 compiles selected research tasks into deterministic, offline and
allowlisted jobs. It deliberately does not execute arbitrary Python, shell
commands, network requests, external solvers or proof assistants.

## OAK status

`CERTIFIED_OFFLINE_JOB_RUNNER_FIXTURE_R0_7` certifies deterministic behavior of
the built-in software fixtures and their replay audit. It does not certify a
mathematical theorem, scientific discovery, solver completeness, Lean kernel
acceptance, novelty, publication or solution of an open problem.

## Runner allowlist

### `exact_expression`

Evaluates an arithmetic expression using exact rational arithmetic. Allowed
syntax is limited to integer constants, parentheses, unary signs and the
operators `+`, `-`, `*`, `/`, `//`, `%` and bounded nonnegative powers.

Names, function calls, attributes, indexing, comprehensions, imports and other
Python syntax fail closed.

### `interval_polynomial`

Evaluates a polynomial over a finite decimal interval through outward-rounded
interval Horner propagation. The receipt contains lower and upper bounds and an
independent recomputation receipt. This is an interval enclosure, not a proof
of an unrelated theorem.

### `sat_certificate`

Checks a supplied Boolean assignment against a finite CNF clause set. It does
not invoke a SAT solver. A satisfying assignment receives a verified Boolean
certificate; an invalid assignment becomes `invalid_certificate` and enters
M−.

### `lean_skeleton`

Performs structural validation only. It checks declaration shape, delimiters
and forbidden placeholders such as `sorry`, `admit`, `axiom` and `unsafe`.
It explicitly emits `kernel_checked: false`; it is not a substitute for Lean.

## Safety and execution policy

Every bundle environment lock must set:

```json
{
  "network_access": false,
  "arbitrary_subprocess": false
}
```

Every job must also set `network_access: false` and
`external_execution: false`. Jobs require:

- stable identifiers;
- canonical problem and optional claim identity;
- method and exact scope;
- stopping rule;
- deterministic seed;
- finite operation, input and output budgets;
- error contract;
- license note;
- no proof or solution claim.

Runtime budgets are finite campaign controls, not permanent atlas ceilings.

## Bundle example

```json
{
  "schema": "omega-problem-job-bundle/7",
  "campaign_id": "campaign-001",
  "environment_lock": {
    "contract_version": "omega-problem-runners/7",
    "network_access": false,
    "arbitrary_subprocess": false,
    "runner_implementation": "python-standard-library-builtins"
  },
  "jobs": []
}
```

## Run

```bash
omega-problem-jobs compile \
  --bundle-json campaigns/campaign_001.json \
  --output-dir generated/campaign_001
```

Create a deterministic partial checkpoint:

```bash
omega-problem-jobs compile \
  --bundle-json campaigns/campaign_001.json \
  --output-dir generated/campaign_001 \
  --max-jobs 32
```

Resume:

```bash
omega-problem-jobs compile \
  --bundle-json campaigns/campaign_001.json \
  --output-dir generated/campaign_001 \
  --resume
```

The final materialization after interruption and resume is byte-identical to an
uninterrupted execution of the same bundle and environment contract.

Audit:

```bash
omega-problem-jobs audit generated/campaign_001
```

Replay one job from the materialized campaign:

```bash
omega-problem-jobs replay \
  --campaign-dir generated/campaign_001 \
  --job-id job.example
```

## Outputs

```text
job_specs.jsonl
job_receipts.jsonl
campaign_events.jsonl
mminus_records.jsonl
checkpoint.json
manifest.json
report.json
```

### Job receipts

Each receipt records:

- input, output, stdout and stderr digests;
- exact status and certificate status;
- operation counts for generator and verifier;
- verifier identity;
- resource and error contracts;
- replay contract;
- policy decision;
- zero network and external execution;
- zero theorem promotion, proof and solution claims.

### Campaign events

Events use deterministic logical sequence numbers rather than wall-clock times.
This preserves byte-identical replay and avoids pretending that timestamps are
scientific evidence.

### Checkpoints

The checkpoint preserves completed and remaining job IDs, bundle digest,
environment-lock digest and finite runtime batch limit. A mismatched or altered
checkpoint cannot be resumed.

### M− negative memory

`failure`, `invalid_certificate` and `blocked` receipts generate immutable M−
records. A failed calculation therefore remains useful and cannot disappear
silently from a later campaign.

## Strict audit

The audit:

- verifies every file, manifest, report and checkpoint digest;
- checks that completed jobs form the deterministic prefix;
- reexecutes each completed job;
- compares complete receipts byte-for-byte;
- reconstructs events and M− records;
- checks all cardinalities and policies;
- rejects any network, subprocess, theorem-promotion, proof or solution claim.

## Deliberate limitations

R0.7 does not yet run Z3, cvc5, external SAT solvers, SageMath, SymPy,
Mathematica, Lean, Coq, Isabelle, GPU kernels or PDE solvers. Such adapters must
be isolated, version-locked and separately authorized in future layers.

## Next layer

R0.8 should update portfolio routing only from append-only evidence events and
M− outcomes, with explainable score deltas and deterministic replay from
campaign genesis.
