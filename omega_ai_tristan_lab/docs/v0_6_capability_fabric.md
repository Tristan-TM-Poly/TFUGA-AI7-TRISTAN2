# Ω-TRISTAN-RUNTIME-T∞ — v0.6 Capability Fabric

## Goal

v0.6 changes the integration unit from a repository or Python package into a **capability with provenance, policy, schemas, and reproducible execution evidence**.

```text
repository
→ package/adapter
→ capability manifest
→ capability graph
→ policy gate
→ execution
→ TIR artifact
→ execution capsule
→ OAK evidence
```

This is intentionally incremental: v0.3 plugins remain valid. Legacy `capabilities() -> Sequence[str]` plugins are lifted automatically into rich `CapabilitySpec` objects until their repository gets a native manifest.

## 1. TIR

`tir.py` introduces `Provenance`, `Uncertainty`, `TristanArtifact`, and deterministic semantic SHA-256 digests. A runtime result can therefore travel across future Python/Rust/C++ backends without losing its source and validation state.

## 2. Capability graph

A capability is described by `CapabilitySpec`:

```python
CapabilitySpec(
    id="tristan.idea.analyze",
    task="idea-report",
    input_kind="idea",
    output_kind="analysis-report",
    permissions=("PURE",),
)
```

`CapabilityGraph` resolves providers independently from repository names. This allows several implementations of the same capability later.

## 3. Least-privilege PolicyKernel

The first permission vocabulary is `PURE`, `FILESYSTEM_READ`, `FILESYSTEM_WRITE`, `NETWORK_READ`, `GITHUB_READ`, `GITHUB_WRITE`, `EXTERNAL_ACTION`, and `IP_SENSITIVE`.

The default execution context grants only `PURE`. A capability asking for network or write access is blocked unless a caller supplies an explicit execution context. This is the runtime form of ZERO-TOUCH without zero-control.

## 4. Execution capsules

`execute_capability()` now emits raw output, a TIR artifact, input/output digests, provider/source, policy decision, Python/platform metadata, execution duration, and a replay-oriented capsule identifier.

Capsules can be persisted as:

```text
capsule/
├── manifest.json
├── input.json
└── output.json
```

## 5. AdapterForge

`AdapterForge` performs local, static inspection only: `pyproject.toml`, `setup.py`, `src/`, candidate import packages, Python-file count and console scripts.

It generates a proposed capability manifest and a deliberately non-executable adapter scaffold. The generated `run()` raises `NotImplementedError` until a human/OAK-reviewed mapping connects capabilities to verified callables.

No clone, install, push, publication, or source-tree mutation occurs during `inspect()` or `plan()`.

```bash
omega-tristan-runtime adapter-plan /path/to/repository
```

## 6. Capability execution

```python
from omega_ai_tristan_lab import TristanRuntime
from omega_ai_tristan_lab.plugin import plugin

runtime = TristanRuntime(auto_discover=False)
runtime.register(plugin)
execution = runtime.execute_capability(
    "tristan.idea.analyze",
    {"idea": "Generate and falsify a measurable prototype"},
)
print(execution.artifact.id)
print(execution.capsule.output_digest)
```

A capability pipeline can be composed independently of plugin names:

```python
runtime.capability_pipeline(
    ["system.generate", "system.simulate", "oak.validate"],
    payload,
)
```

## 7. Doctor maturity

The repository doctor now exposes a normalized packaging maturity score and concrete next actions. This score measures integration readiness only; it does not imply scientific correctness.

## 8. Reproducible wheel CI

GitHub Actions now:

1. installs development dependencies;
2. runs all tests;
3. smoke-tests the capability graph;
4. builds wheel + sdist;
5. installs the wheel into a clean virtual environment;
6. smoke-tests the installed CLI;
7. uploads wheel/sdist as workflow artifacts.

## OAK invariants

- No hidden repository cloning or package installation in the runtime.
- No execution of generated adapters before callable mappings are reviewed.
- Network/write capabilities are blocked by default.
- A successful execution is `EXECUTED_UNVERIFIED`, not scientific proof.
- Provenance and hashes accompany executable results.
- Existing v0.3 plugins remain compatible.
- Capability declarations must not overclaim tasks that `run()` cannot execute.

## Next wave

The next highest-value proof is not another framework layer. It is to adapt at least three real repositories to native `CapabilitySpec` manifests and make one cross-repository pipeline pass differential tests end-to-end.
