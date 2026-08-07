# Ω-AI-TRISTAN-LAB v0.3 — Multi-repository Python runtime

## Goal

Turn Tristan's GitHub repositories into one composable Python execution surface
without physically merging the repositories.

```text
GitHub repositories
      ↓
per-repo Python package / adapter
      ↓
tristan.plugins entry points
      ↓
TristanRuntime
      ↓
run / pipeline / doctor
```

The runtime is intentionally **network-free by default**. It never clones a
repository, installs a package, publishes code, or runs a remote action merely
because it was imported.

## Repository registry

`RepoRegistry` tracks the six repositories visible during the v0.3 audit:

- `PEFA-FractalEnergySystem`
- `TFACC`
- `TFUGA-AI7-TRISTAN2`
- `Tristan_Tardif-Morency_TFUG`
- `Tristan_Tardif-Morency_TFUGAG`
- `TTM-TFUGA-AI7-TRISTAN2`

Run:

```bash
omega-tristan-runtime repos
omega-tristan-runtime doctor
omega-tristan-runtime plugins
```

`doctor` distinguishes:

- `installed`: the declared Python distribution exists in the active interpreter;
- `not-installed`: packaging metadata exists, but the distribution is absent;
- `needs-packaging`: the repository still needs a root distribution/adapter.

## Plugin contract

Every repository can join the runtime with a tiny adapter:

```python
class PEFAPlugin:
    name = "pefa"

    def capabilities(self):
        return ("simulate", "benchmark")

    def run(self, task, payload):
        ...
```

and in that repository's `pyproject.toml`:

```toml
[project.entry-points."tristan.plugins"]
pefa = "pefa_tristan.plugin:plugin"
```

No central registry code must change when a new package is installed.

## One-process execution

```python
from omega_ai_tristan_lab import PipelineStep, TristanRuntime

lab = TristanRuntime()
print(lab.plugins())

report = lab.run(
    "omega-ai-tristan-lab",
    "idea-report",
    {"idea": "Build a reproducible detector simulation"},
)

result = lab.pipeline(
    [
        PipelineStep("system-a", "generate"),
        PipelineStep("system-b", "simulate"),
        PipelineStep("system-c", "oak"),
    ],
    {"input": "..."},
)
```

## Current OAK status

The registry does not pretend that every repository is already installable.

- `TFUGA-AI7-TRISTAN2` already declares distribution `tfuga-ai7-tristan2`.
- `TTM-TFUGA-AI7-TRISTAN2` already declares `tristan-omni-core`.
- `Tristan_Tardif-Morency_TFUG` has a root package focused on
  `protein-fold-tristan`, not yet the entire corpus.
- `PEFA-FractalEnergySystem` has `src/` and tests but its current root
  `pyproject.toml` contains pytest configuration rather than full project
  metadata.
- `TFACC` and `Tristan_Tardif-Morency_TFUGAG` still need root packaging or a
  thin adapter.

This is deliberate: v0.3 creates the execution **contract first**, then each
repository can be migrated independently without a destructive mega-merge.

## Next migration wave

For each repository:

1. add/repair `[build-system]` and `[project]`;
2. expose one stable Python package;
3. implement one `TristanPlugin`;
4. register it under `tristan.plugins`;
5. add unit tests and a runtime smoke test;
6. build a wheel in CI;
7. pin versions in an integration bundle.

The end state is a reproducible environment in which ChatGPT or any Python
worker can install the bundle once and execute all compatible Tristan systems
through the same API.
