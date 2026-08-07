# Ω-TRISTAN-RUNTIME v0.9 — Contract & Trust Fabric

v0.9 hardens the v0.8 four-repository execution fabric without rewriting the historical R07/R08 evidence locks.

## New gates

1. **SchemaGraph** — capabilities can declare machine-checkable input/output schemas.
2. **PipelineCompiler** — capability sequences are compiled before execution and schema-incompatible chains fail closed.
3. **Discovery M⁻** — broken entry points are retained as structured failures; `oak-strict` refuses silent loss.
4. **Runtime provenance** — discovered distribution/version/repository/VCS commit are propagated into TIR artifacts when available.
5. **Parent lineage** — capability pipelines link each artifact to the previous artifact digest.
6. **ExecutionSandbox** — bounded subprocess, timeout, temporary working directory, reduced environment, POSIX memory ceiling when available, and user-space network denial for PURE execution.
7. **SupplyChainOAK** — installed-package inventory plus offline wheelhouse hash verification.
8. **EnvironmentMatrix** — platform targets are explicit objects; a declared target is never treated as a verification receipt.

## OAK boundaries

- `USER_SPACE_BOUNDED` sandboxing is **not** a certified security boundary.
- Vulnerability status is `NOT_SCANNED_NO_VULNERABILITY_DB` unless a separately governed vulnerability database is used.
- Legacy plugins remain executable through `tristan.any`; schema-strict behavior requires explicit schema contracts.
- Historical integration receipts remain immutable evidence of the exact versions that produced them.

## CLI

```bash
omega-tristan-runtime discovery-report --mode oak-strict --expect omega-ai-tristan-lab
omega-tristan-runtime schemas --json
omega-tristan-runtime compile-pipeline tristan.idea.analyze --initial-schema tristan.idea.v1
omega-tristan-runtime find-pipeline tristan.idea.v1 tristan.analysis-report.v1
omega-tristan-runtime run-sandboxed tristan.idea.analyze --payload-json '{"idea":"test"}'
omega-tristan-runtime supply-chain
omega-tristan-runtime environment
```
