# Ω-TRISTAN-RUNTIME v0.7 — Exact-Pinned Cross-Repository Integration

v0.7 now contains a **CI-verified integration profile** across three real repositories.

```text
PEFA-FractalEnergySystem
  pefa-omega-em2.cvcd-extract
        ↓
TTM-TFUGA-AI7-TRISTAN2
  tristan-omni-core.evidence-to-idea
        ↓
TFUGA-AI7-TRISTAN2 / Ω-AI-TRISTAN-LAB
  tristan.idea.analyze
        ↓
TIR + ExecutionCapsules + OAK analysis
```

## Exact source pins used by the verified run

| Component | Exact commit | Version in run |
|---|---|---|
| PEFA driver/adapter | `04914785353d3db59af36e57f5c19b3a75b74f1f` | `pefa-fractal-energy-system==0.1.1` |
| Omni-Core adapter | `29e77ad2e1214eb536043b31670071f5079285a5` | `tristan-omni-core==0.2.1` |
| Tristan Runtime | `6f0c46401be32823e4370ed6bdae699955d81ca3` | `omega-ai-tristan-lab==0.7.0` |

No `main`, `master`, or moving feature-branch reference was used to install the two public peers during the verification run.

## CI evidence receipt

The exact-pinned pipeline completed successfully in GitHub Actions:

- repository: `Tristan-TM-Poly/PEFA-FractalEnergySystem`
- workflow: `Tristan Runtime Adapter R0.1`
- run: `31192063344`
- artifact: `8999236642`
- artifact SHA-256: `83f07f9293b908d1f628c10ef9139f9f65c9ecb02a5a4b4c1220294416856341`
- machine marker: `CROSS_REPO_PIPELINE_PINNED_PASS`

The uploaded artifact contains the PEFA distribution artifacts plus `out/cross_repo_pipeline.json`.

`IntegrationEvidence` now validates the evidence IDs, 40-hex source commits and 64-hex artifact digest before a profile is allowed to carry a `CI_VERIFIED*` status.

## What the verified workflow actually exercised

1. checked out exact PEFA head;
2. installed PEFA including explicit `numpy>=1.26` runtime dependency;
3. ran the focused PEFA adapter tests;
4. built PEFA wheel + sdist;
5. installed exact runtime commit `6f0c464...`;
6. installed exact Omni-Core commit `29e77ad...`;
7. asserted package versions `0.1.1`, `0.2.1`, `0.7.0`;
8. discovered the three capabilities through `tristan.plugins`;
9. executed the capability pipeline in order;
10. required the final output to contain an OAK report;
11. persisted the pipeline report and uploaded it as an Actions artifact.

## M-minus caught during migration

The first PEFA adapter CI attempt exposed an undeclared dependency: importing the historical PEFA package initializer reaches `mft_simulator`, which imports NumPy. Rather than bypassing that path or weakening the test, PEFA packaging was corrected to declare `numpy>=1.26`, then the workflow was rerun successfully.

This failure remains useful negative memory: packaging must describe the transitive import behavior actually exercised by a clean environment.

## CLI

```bash
omega-tristan-runtime integration-lock
```

The command is read-only. By default it emits only public peer installation targets. The private PEFA target is included only when explicitly requested:

```bash
omega-tristan-runtime integration-lock --include-private-targets
```

Neither command authenticates, clones, installs, pushes, merges, or publishes anything.

## OAK boundary

`CI_VERIFIED_CROSS_REPO_R01` means the exact-pinned software composition ran successfully. It proves a much stronger software fact than a design document, but it still does **not** prove:

- physical validity of PEFA/CVCD models;
- independent scientific reproduction;
- truth of an OAK-generated claim;
- product-market fit or economic value;
- patentability;
- security certification;
- permission to merge any adapter branch to a default branch.

PEFA and Omni-Core therefore remain `adapter-candidate` in `RepoRegistry`, even though their exact commits have been exercised successfully by the integration pipeline.

## Next crystallization gate

The next high-value step is to repeat this pattern for a fourth real system, preferably one with a different dependency shape, then build a bundle/wheelhouse from immutable locks rather than from source branches.
