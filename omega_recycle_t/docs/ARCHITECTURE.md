# Ω-RECYCLE-T∞ Architecture

## Layer 0 — Provenance

`MaterialPassport` stores product identity, schema version, component inventory and source provenance.

## Layer 1 — ResourceGraph

A product is represented as components plus hyperedges such as fastening, enclosure, electrical coupling or shared material relationships.

## Layer 2 — Recovery candidates

Each component receives explicit route candidates: reuse, repair, remanufacture, component harvest, material recycling, energy recovery or disposal.

## Layer 3 — Transparent scoring

`evaluate_route` separates recoverable functional/material value, process and disassembly costs, energy shadow cost, risk penalty, externality penalty, structure-preservation bonus and expected future-cycle contribution. Every coefficient remains visible and replaceable.

## Layer 4 — Optimization

R0.1 uses deterministic independent component selection. Future releases can lift this into a constrained hypergraph flow problem:

max_x sum(i,r) x(i,r) J(i,r)

subject to exactly-one-route, capacity, compatibility, transport, inventory, emissions and safety constraints.

## Layer 5 — OAK

`audit_plan` distinguishes executable software from scientific/industrial evidence and forces hazardous or certified-process routes into simulation-only status.

## Extension map

```text
R0.1 core
├── Recycle-CVCD: compress products to recovery-relevant invariants
├── UrbanMine: spatiotemporal material-stock graph
├── Symbiosis: output-to-input industrial matching
├── BAT-Recycle: certified battery second-life decision support
├── Electronics-Mine: component-first e-waste recovery
├── Building-Mine: reversible building material passports
└── Recycle-Bayes: uncertainty-aware route switching
```
