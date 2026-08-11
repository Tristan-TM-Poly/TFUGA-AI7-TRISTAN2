# Ω-SKILLGEN-T∞ — Civilization layer

The civilization layer makes the foundry reason about an entire skill ecology rather than isolated manifests.

## Adversarial eval compiler

Declared invariants, tool policies, and `do_not_use_when` boundaries are automatically compiled into negative/adversarial regression candidates. This converts passive prose constraints into executable evaluation obligations.

## Lineage DAG

Fusion, fission, M- repair, and later mutations create explicit parent/child lineage. `lineage_audit` checks the candidate genealogy for cycles, external parents, and a topological rollback order. Acyclic provenance supports recovery and auditability; it does not prove behavior.

## Expansion planner

Given a desired capability map and the current SkillSpecs, the planner emits generation tasks only for lexically uncovered capabilities. Each task carries required OAK gates and `auto_promote=false`. This prevents generating thousands of redundant skills merely to increase count.

## Meta-loop

`desired capabilities → ecology coverage → gap tasks → domain generators → candidate families → adversarial evals → SkillGenome/CVCD → Pareto arena → behavioral telemetry → M+/M- → lineage DAG → promotion ledger`

This turns Ω-SKILLGEN into a controlled skill civilization compiler while preserving the distinction between generated architecture and demonstrated capability.
