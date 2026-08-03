# Ω-SYNERGY-T∞ implementation architecture

## Packages

| Module | Responsibility |
|---|---|
| `models` | Typed authority, CreationDNA, interfaces, tensors, experiments, PR genes and products |
| `ontology` | System IDs, domains, transformations, types, evidence and risk extraction |
| `scanner` | Bounded multi-repository ingestion |
| `graph` | CreationGraph, edges, closure paths and DOT/JSON export |
| `scoring` | Multi-objective tensor, candidate construction, Shapley and half-life |
| `discovery` | Pair discovery, beam search, closure bridges and portfolio optimization |
| `experiments` | Baselines, ablations, controls, counterfactual twins and OAK gates |
| `ledger` | Append-only proof records and revalidation policy |
| `meta` | Typed composition of primitive synergies |
| `pr_orchestra` | PRGenome, dependencies, conflicts and review waves |
| `product` | Conservative offer hypotheses and blockers |
| `reporting` | Complete review bundle and compatibility aliases |
| `cli` | Stable command-line surface |

## Data flow

```text
file
  -> IDs + domains + tokens + transformations + risks
  -> CreationDNA
  -> capability/need matcher
  -> InterfaceContract
  -> SynergyTensor
  -> SynergyCandidate
  -> ExperimentPlan + CounterfactualTwin
  -> PRGene + ProofLedger
  -> MetaSynergy + ProductHypothesis
```

## Determinism

Stable identifiers are SHA-256-derived from normalized structural inputs. Search ordering uses score then lexical identifiers. CI should use a fixed Python version and frozen repository commits for fully reproducible reports.

## Extension contracts

New extractors should output `Capability`, `Need`, `EvidenceRecord` or `InterfaceContract` objects rather than mutate scores directly. New scoring dimensions must remain explicit and receive a negative-control test. New remote actuators must be implemented outside the read-only Foundry and pass Ω-ACTION-EXT-T gates.

## Performance strategy

The scanner bounds file size, text length and node count. Pair generation uses domain/token buckets rather than all-pairs enumeration. Higher-order search uses a beam. Future scale work may add SQLite indexes, incremental commit diffs and sparse vector search without changing the evidence authority.
