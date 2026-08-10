# Ω-ACTIONS-T∞ — R0.5 CacheTensor + R0.7 CI-IR Compiler

This wave converts two remaining architectural ideas into executable, testable kernels.

## R0.5 — CacheTensor empirical value

A cache is useful only if avoided work exceeds restore/save overhead.

For cache policy `k`:

```text
V_k = hits_k * saved_seconds_per_hit_k
      - restore_seconds_total_k
      - save_seconds_total_k
```

The implementation also derives hit rate, net seconds per attempt, overhead per attempt and a gross-value/overhead ratio.

Decisions are intentionally evidence-aware:

- `KEEP_OR_EXPAND` when measured/declared net value is positive;
- `REMOVE_OR_REDESIGN` when overhead dominates;
- `INSUFFICIENT_EVIDENCE` when fewer than five attempts are available.

The five-attempt threshold is a provisional evidence gate, not a universal statistical law. Future UNC² integration should replace it with explicit credible intervals and uncertainty half-life.

### Input example

```json
{
  "caches": [
    {
      "name": "pip",
      "attempts": 20,
      "hits": 16,
      "restore_seconds_total": 30,
      "save_seconds_total": 10,
      "saved_seconds_per_hit": 8
    }
  ]
}
```

### CLI

```bash
omega-actions-cache cache_observations.json \
  --json-out CACHE_TENSOR.json \
  --markdown-out CACHE_TENSOR.md
```

Equivalent unified dispatcher:

```bash
python -m omega_actions_t cache cache_observations.json
```

### OAK rules

Cache timing value never overrides supply-chain, poisoning, confidentiality, provenance or reproducibility constraints. Secrets are never cache payloads.

## R0.7 — CI Intermediate Representation

Hand-maintained YAML is treated as a compilation target rather than the primary architecture.

```text
CI intent
  -> CI IR
  -> validation
  -> deterministic compiler
  -> GitHub Actions YAML
  -> CI/OAK evidence
```

The first IR is intentionally small and strict. It supports:

- workflow name;
- `pull_request`, `push`, `workflow_dispatch`-style empty triggers;
- branches / branches-ignore;
- paths / paths-ignore;
- least-privilege permissions;
- concurrency and cancellation;
- jobs, `needs`, runners and positive timeouts;
- simple matrices and `max-parallel`;
- pinned checkout/setup-python/upload-artifact primitives;
- run steps.

### Example CI IR

```json
{
  "name": "Generated CI",
  "on": {
    "pull_request": {
      "paths": ["src/**", "tests/**"]
    }
  },
  "permissions": {"contents": "read"},
  "concurrency": {
    "group": "ci-${{ github.ref }}",
    "cancel_in_progress": true
  },
  "jobs": [
    {
      "id": "test",
      "runs_on": "ubuntu-latest",
      "timeout_minutes": 10,
      "steps": [
        {"kind": "checkout", "name": "Checkout"},
        {
          "kind": "setup-python",
          "name": "Python",
          "python_version": "3.11",
          "cache": "pip"
        },
        {"kind": "run", "name": "Test", "run": "pytest -q"}
      ]
    }
  ]
}
```

### Compiler invariants

1. Every job has a stable valid ID.
2. Every job has a positive timeout.
3. Every `needs` edge resolves to an existing job.
4. Write/elevated token permissions are rejected by default.
5. Generated path-filtered workflows include their own workflow path so compiler changes can self-validate.
6. Known GitHub actions are emitted using pinned SHAs.
7. Checkout disables persisted credentials in the standard named primitive.
8. Compilation is deterministic: same IR + target path produces the same YAML.
9. The compiler writes a local output only; it does not commit, push, merge or enable workflows.

### CLI

```bash
omega-actions-compile ci-ir.json \
  --workflow-path .github/workflows/generated-ci.yml \
  --out generated-ci.yml
```

or:

```bash
python -m omega_actions_t compile ci-ir.json --out generated-ci.yml
```

## Link with the Digital Twin

The intended pipeline is now executable in pieces:

```text
existing YAML
  -> R0.1 structural analyzer
  -> R0.2 telemetry
  -> R0.3 ΔCI
  -> R0.35 evidence ranking
  -> R0.4 adaptive test sharding
  -> R0.5 empirical CacheTensor
  -> R0.6 Digital Twin
  -> R0.7 CI IR compiler
  -> candidate YAML
  -> before/after OAK validation
```

R0.8 will close the loop by creating candidate patches from evidence, but automatic promotion remains blocked until the candidate beats the baseline with comparable telemetry and has a rollback path.

## Anti-bullshit invariant

```text
compiler output != optimization
predicted improvement != measured improvement
fewer workflows != stronger CI
```

A candidate becomes an optimization only after evidence shows lower redundant compute and/or latency without unacceptable loss of proof, coverage, security or reproducibility.
