# Ω-TRISTAN-RUNTIME v0.8 — Four-Repository Matrix + Reproducible Bundle

v0.8 crystallizes a verified environment rather than adding another abstract orchestration layer.

## Verified environment

The GitHub Actions matrix `31193546089` installed and exercised four exact-pinned distributions in one Python environment:

| Repository | Exact commit | Distribution |
|---|---|---|
| Runtime host — `TFUGA-AI7-TRISTAN2` | `f4f1968b6fd63ec4c2167f79d29701d92e65afa7` | `omega-ai-tristan-lab==0.7.0` |
| PEFA | `1e72e4619c3fb2b2c175f23ae8053d752a709621` | `pefa-fractal-energy-system==0.1.1` |
| Omni-Core | `29e77ad2e1214eb536043b31670071f5079285a5` | `tristan-omni-core==0.2.1` |
| TFUG Protein | `42c3467b2675c7d83beae6b274586dc2cdf77d42` | `protein-fold-tristan==0.2.1` |

Evidence:

- run: `31193546089`
- artifact: `8999841064`
- SHA-256: `ddff439b450870965fc7a4b103ced0c3955890dda55bc08ceeaffd18f8961b41`
- marker: `FOUR_REPO_RUNTIME_PINNED_PASS`

The artifact contains PEFA build artifacts and `out/four_repo_matrix.json`.

## What was actually executed

Two bounded probes ran in the same environment.

### 1. PEFA → Omni → OAK pipeline

```text
pefa-omega-em2.cvcd-extract
→ tristan-omni-core.evidence-to-idea
→ tristan.idea.analyze
```

The workflow asserted provider order and required a final `oak_report`.

### 2. Independent Protein probe

```text
protein-fold-tristan.sequence-validate
```

The workflow asserted `provider == protein-fold-tristan`, a valid result for the synthetic canonical amino-acid fixture, and the explicit boundary `COMPUTATIONAL_VALIDATION_ONLY`.

Protein is deliberately **not** represented as a fourth PEFA/OAK pipeline stage. The runtime proves shared software composition, not a cross-domain scientific causal link.

## M⁻ captured

Two failures improved the system rather than being hidden:

1. PEFA initially lacked an explicit NumPy dependency reached by its historical eager package initializer. `numpy>=1.26` was added to packaging; the test was not weakened.
2. The first four-repository matrix asserted nonexistent `CapabilityExecution.plugin/result` attributes. The real API is `provider/output`; workflows were corrected without changing runtime semantics.

## R0.8 lock

`integration/tristan_runtime_r08.lock.json` records:

- runtime host commit;
- three exact peer commits;
- two distinct probes;
- GitHub Actions receipt;
- artifact digest;
- OAK non-claims.

`DEFAULT_R08_LOCK.validate()` rejects floating refs and also rejects any attempt to insert Protein validation into the PEFA semantic pipeline.

## BundlePlan

v0.8 introduces a side-effect-bounded bundle planner:

```bash
omega-tristan-runtime bundle-plan
omega-tristan-runtime bundle-plan --output-dir build/tristan_bundle
```

The generated public bundle contains:

```text
build/tristan_bundle/
├── bundle-manifest.json
└── requirements-public.lock
```

PEFA is private and therefore excluded from the public requirements file. It is materialized only by explicit request:

```bash
omega-tristan-runtime bundle-plan \
  --output-dir build/tristan_bundle_private \
  --include-private-extension
```

which additionally creates `requirements-private-extension.lock`.

Generating these files performs no install, clone, authentication, GitHub action or publish operation.

## Public wheelhouse CI

The v0.8 central CI now goes beyond source installs:

1. build `omega-ai-tristan-lab==0.8.0` wheel;
2. build wheels from exact Omni and Protein commits plus their dependencies;
3. collect them in `public_wheelhouse/`;
4. create a fresh virtual environment;
5. install with `--no-index --find-links public_wheelhouse`;
6. rediscover runtime/Omni/Protein capabilities;
7. execute the Protein validation probe offline from the local wheelhouse;
8. hash every wheel;
9. upload wheelhouse + bundle manifest as one Actions artifact.

This is the first step from "repositories that can interoperate" toward "a portable local Tristan Python library bundle".

## OAK boundary

`CI_VERIFIED_FOUR_REPO_R02` proves exact-pinned software co-installation and bounded execution. It does not prove physics, biological function, clinical meaning, independent scientific reproduction, market value, patentability, security certification, or merge readiness.

PEFA, Omni and Protein adapters remain `adapter-candidate`; their default branches remain untouched.
