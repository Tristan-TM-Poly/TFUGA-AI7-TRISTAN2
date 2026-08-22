# Prior-art map — Literature Court R1

Status: **active and incomplete**. This file identifies nearest neighbors; it does not establish novelty.

## Repository organization

`potvin2016monorepo` is a strong baseline for very-large-scale repository organization and the trade-offs of a monolithic source repository. The thesis must compare Repo Fabric against mature monorepo and polyrepo integration rather than treating large-scale source coordination as an empty field.

## Software architecture abstractions

`shaw1995architecture` is a foundational baseline for architecture-level components, interactions and configuration constraints. Typed RepoCells or CapabilityCells are therefore not novel merely because they exist above functions and files.

## Intermediate representations

`lattner2020mlir` is a strong nearest neighbor for reusable and extensible intermediate representations across multiple abstraction levels and implementations. Capability IR must justify any material difference in terms of provider-independent task semantics, evidence/uncertainty contracts, routing and cross-repository composition.

## Proof-carrying artifacts

`necula1997pcc` is the canonical baseline for code accompanied by machine-checkable proof of adherence to a safety policy. The thesis must not transfer PCC's proof semantics to a broader repository evidence passport. A Proof-Carrying Repository is currently a different, weaker architectural construction containing commit, claims, evidence, uncertainty, provenance, security and limits.

## Executable runtime models

`vogel2018runtime` and `vogel2018megamodels` are close neighbors for executable runtime megamodels, explicit feedback loops and relations among runtime models. Claims around living/executable architectural graphs must therefore compare directly with models-at-runtime research.

## Scientific workflow systems

`crusoe2021cwl` and the Common Workflow Language specification provide mature prior art for portable, declarative workflows that compose heterogeneous tools. `sutera2025workflowterminology` further provides a modern community terminology spanning workflow characteristics, composition, orchestration, data management and metadata capture.

Consequently, Intent-to-RepoGraph is not novel merely because it composes heterogeneous software. Candidate differences to test include semantic capability demand, provider resolution under evidence/uncertainty constraints and the bidirectional theory/code layer.

## Provenance and research-object packaging

`lebo2013provo` provides a W3C Recommendation for interoperable provenance. `soilandreyes2021rocrate` and `leo2023workflowrunrocrate` describe research-object and workflow-run packaging that connects data, software, workflows and provenance.

EvidenceReceipt should therefore map to established provenance concepts wherever possible. Carrying provenance is not itself a novelty claim. The candidate research delta is its coupling to typed claims, capability routing, OAK state and semantic/scientific validation.

## Contribution-level court

Do not evaluate the entire system as one giant novelty claim. Evaluate each candidate independently:

| Candidate | Nearest baseline family | Status |
|---|---|---|
| CapabilityCell | architecture/components + workflow interfaces | HOLD |
| Capability IR | MLIR + workflow portability + service contracts | HOLD |
| Executable hyperedge | workflow/runtime execution + graph models | HOLD |
| Proof-Carrying Repository | PCC + PROV-O + RO-Crate | HOLD |
| Semantic/Scientific CI | schema/type validation + scientific workflow practice | HOLD |
| Theory-to-Repo Compiler | model-driven engineering + workflow generation | HOLD |
| Repo-to-Theory Compiler | program/specification analysis | HOLD |
| Theory-Code semantic diff | bidirectional transformation | HOLD |
| Mycelial fixed-point test | reproducible/self-describing systems | HOLD |
| Residual-to-Theory compiler | hypothesis generation + discriminating experiments | HOLD |

## OAK decision rule

For every candidate contribution require:

```text
nearest prior art
-> shared structure
-> material difference
-> why difference matters
-> executable discriminator
-> negative control
-> evidence
-> limitations
-> novelty status
```

Until that chain is complete, novelty remains `HOLD`.
