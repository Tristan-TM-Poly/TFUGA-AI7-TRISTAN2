# Ω-TRISTAN-RUNTIME v1.0 — Fully Typed Multi-Repository Fabric

## Purpose

v1.0 closes the principal PEFA → Omni → OAK pipeline with explicit, machine-checkable schemas while preserving repository independence.

Peer repositories do **not** import the central runtime merely to describe capabilities. They publish structural schema/capability mappings through their existing `tristan.plugins` entry point. The runtime normalizes those declarations into its canonical `SchemaSpec` and `CapabilitySpec` objects and fails closed on malformed declarations.

## Typed four-repository target

The principal path is:

```text
tristan.pefa.cvcd-observation-batch.v1
  → pefa-omega-em2.cvcd-extract
tristan.evidence.cvcd-invariant.v1
  → tristan-omni-core.evidence-to-idea
tristan.idea.v1
  → tristan.idea.analyze
tristan.analysis-report.v1
```

No `tristan.any` wildcard is permitted on this v1.0 critical path.

Protein remains an independent fourth-repository probe with explicit schemas for sequence validation, contact-map calculation and OAK evidence-level estimation.

## Structural peer contract

A peer can expose plain mappings:

```python
def schema_specs(self):
    return ({
        "id": "example.input.v1",
        "kind": "mapping",
        "required_keys": ("value",),
        "allow_extra": True,
    },)


def capability_specs(self):
    return ({
        "id": "example.transform",
        "task": "transform",
        "input_schema": "example.input.v1",
        "output_schema": "example.output.v1",
        "permissions": ("PURE",),
        "deterministic": True,
    },)
```

The central runtime performs structural coercion. Missing required contract fields, incompatible duplicate schemas, schema mismatches and invalid output payloads fail closed.

## Pipeline synthesis

`PipelineCompiler.find_path()` can derive a schema-compatible sequence rather than requiring a manually authored chain. The v1.0 integration gate requires the automatically discovered route from the PEFA batch schema to the Tristan analysis-report schema to equal the intended three-step route.

This is a capability-graph planner, not an autonomous authority layer. Policy permissions, OAK boundaries and explicit execution remain separate.

## Versioned peers

The v1.0 integration target uses:

- `pefa-fractal-energy-system==0.1.2`
- `tristan-omni-core==0.2.2`
- `protein-fold-tristan==0.2.2`
- `omega-ai-tristan-lab==1.0.0`

Exact source commits are pinned by the integration workflow and must be copied into the execution receipt.

## OAK gates

A v1.0 receipt may claim only what the workflow directly proves:

- exact-pinned package builds;
- offline installation from the generated wheelhouse;
- plugin discovery;
- shared-schema convergence;
- absence of `tristan.any` on the selected critical path;
- path synthesis and explicit compilation agreement;
- runtime input/output schema validation;
- artifact lineage/provenance fields;
- wheel SHA-256 verification.

It does **not** prove scientific truth, physical validity, biological function, clinical meaning, certified sandbox isolation, absence of vulnerabilities, commercial value or patentability.

## Compatibility

Legacy plugins without rich schemas continue to be lifted through `tristan.any`; this is backward compatibility, not v1.0 certification. The four-repository v1.0 receipt distinguishes the typed critical path from the wider legacy ecosystem.
