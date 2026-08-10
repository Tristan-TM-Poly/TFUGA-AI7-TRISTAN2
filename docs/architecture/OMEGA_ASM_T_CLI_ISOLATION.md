# Ω-ASM-T∞ — CLI Isolation in the Monorepo

## Problem

The repository root `pyproject.toml` is a shared packaging manifest watched by many otherwise path-aware subsystem workflows.

Registering a single new root entry point such as:

```toml
omega-asm = "omega_asm_t.cli:main"
```

makes an ASM-only pull request also change `pyproject.toml`. Every subsystem workflow whose `paths:` list includes that shared file can then become eligible, even when no files in that subsystem changed.

For Ω-ASM-T this created a large queue of unrelated RE, VLA, propulsion, mail, revenue, legal and other courts. The problem is tracked repo-wide in issue #312.

## R1 isolation rule

Ω-ASM-T therefore keeps the root packaging manifest byte-for-byte identical to `main` while the feature is developed as a stacked research branch.

Canonical invocation inside the repository is:

```bash
python -m omega_asm_t capabilities
python -m omega_asm_t demo --width 8
```

A repository-local executable launcher is also provided:

```bash
./scripts/omega-asm capabilities
./scripts/omega-asm report --width 8
```

The launcher contains no duplicate command logic; it imports `omega_asm_t.cli.main`.

## Why this is preferable during development

```text
ASM-only change
-> omega_asm_t/** + ASM tests/docs/workflow
-> ASM courts
```

instead of:

```text
ASM-only change
-> shared pyproject.toml
-> dozens of subsystem courts
-> runner saturation
-> delayed evidence
```

This does not imply that root installation can never expose `omega-asm`. It means that a global packaging change should be made deliberately in a packaging/release PR where the cross-repository CI fan-out is expected and useful.

## CI contract

The R1 workflow verifies both supported repository-local invocation surfaces:

```text
python -m omega_asm_t ...
./scripts/omega-asm ...
```

The launcher must be executable and must successfully emit the capabilities JSON.

## OAK interpretation

Reducing irrelevant CI is not weakening evidence. The goal is the opposite: route each change to the smallest sufficient court while preserving explicit shared/integration gates where they are actually needed.

Global integration, packaging and release changes can still trigger broad certification. Subsystem-only branches should not acquire broad authority or broad CI cost solely because they added one CLI alias to a shared manifest.
