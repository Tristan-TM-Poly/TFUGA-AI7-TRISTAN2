# Ω-THESIS-2N-GIT-T — Thesis Factory for Tristan systems

**Status:** B/C — canon doctrine plus executable MVP scaffold.  
**Purpose:** convert each Tristan theory into a living thesis, code package, OAKBench, Git artifact, IP brief, and venture candidate.

## Mother thesis

A Tristan theory is not only text. It is a compressed seed that must expand into `2^n` pages, collapse back into CVCD invariants, generate code, pass OAK validation, and become a Git-tracked product surface.

```text
TheorySeed
  -> LOG compression
  -> CVCD invariant extraction
  -> EXP 2^n PageTree
  -> OAK falsification
  -> CodeGen skeleton
  -> GitPack
  -> IP/Venture map
  -> Canon update
```

## Core objects

### ThesisSeed

A minimal object describing one theory or system:

- `id`: stable canonical identifier, for example `OMEGA_TRANSFORM_T`.
- `name`: human-readable title.
- `status`: OAK maturity, from `A` to `G`.
- `domain`: scientific, software, social, economic, legal, or artistic domains.
- `core_axiom`: phrase-mother of the theory.
- `cvcd_invariants`: compressed invariants that must survive expansion.
- `oak_risks`: hallucination, proof gaps, safety, legal/IP, privacy, scientific overclaim.
- `code_targets`: package, CLI, benchmark, simulator, tests, notebooks.
- `git_targets`: repo, branch, PR, docs, CI, release assets.
- `venture_targets`: product, service, API, patent candidate, licensing path.

### PageTree

A binary expansion tree where each node has a role:

- `LOG`: compression, invariants, definitions, falsifiability.
- `EXP`: expansion, applications, code, examples, venture paths.

Depth rule:

```text
depth n -> 2^n frontier pages, with 2^(n+1)-1 total nodes including root
```

## OAK status gates

| Status | Meaning |
|---|---|
| A | Vision / metaphor / fertile intuition |
| B | Internal doctrine coherent enough to structure work |
| C | Prototype scaffold or code skeleton exists |
| D | Local tests pass |
| E | Benchmarked against external baseline |
| F | Publishable / reusable / documented |
| G | Strong proof, industrial evidence, or production-grade validation |

Rule: a named theory is not a proof. A theory becomes stronger only when definitions, hypotheses, tests, limits, baselines, residues, and negative memory are attached.

## Standard output for each theory

```text
00_manifest/thesis_seed.yaml
01_foundation/phrase_mere.md
02_math/operators.md
03_system/architecture.md
04_code/package_design.md
05_oakbench/falsification_tests.md
06_git/repo_plan.md
07_ip_business/venture_map.md
08_expansion/page_tree.json
```

## Priority branches for first expansion

1. `Ω-TRANSFORM-T` — transform, FFWT, CVCD, compression, anomaly detection.
2. `Ω-FCRYST-T` — fractal crystals, point groups, diffraction and materials.
3. `Ω-PREUVE-T` — fraud/corruption/crime evidence graphs and chain-of-custody.
4. `Ω-AUTO²-T` — automation of automation with dry-run, rollback and sovereignty gates.
5. `Ω-ENERGY-T` — energy systems, losses, storage, conversion and OAK safety.

## Minimal command grammar

```bash
omega-thesis init OMEGA_TRANSFORM_T
omega-thesis expand OMEGA_TRANSFORM_T --depth 8
omega-thesis oak OMEGA_TRANSFORM_T
omega-thesis gitpack OMEGA_TRANSFORM_T
omega-thesis venture OMEGA_TRANSFORM_T
```

## M⁻ negative-memory rules

- No expansion without uncertainty labels.
- No code claim without test target.
- No product claim without user/pain/value hypothesis.
- No scientific claim promoted beyond the evidence level.
- No Git push to protected branches without PR and OAKGate.
- No autonomous destructive action; branch, dry-run, and review path first.
