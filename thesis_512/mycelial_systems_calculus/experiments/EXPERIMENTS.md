# Experimental program — Ω-MYCELIAL-SYSTEMS-CALCULUS-T

All campaigns begin as **planned**. No result is implied until an executable run, configuration, provenance and uncertainty record exist.

## EXP-001 — Coordination scaling

Question: when does capability-registry routing reduce coordination cost relative to manual all-to-all coupling and simpler dependency/service registries?

Variables: repository count, capability count, change rate, lookup rate, contract churn and human-maintenance cost.

Baselines: explicit pairwise integration, static dependency graph, service registry, monorepo-style centralized graph.

Metrics: relation count, configuration edits, breakage rate, routing latency, compute cost and human interventions.

## EXP-002 — Capability substitution

Question: can two providers implementing the same Capability IR be substituted without changing consumers?

Interventions: provider language, implementation, latency, accuracy and failure mode.

Metrics: consumer modifications, contract violations, semantic drift and benchmark delta.

## EXP-003 — Theory-code divergence court

Question: which divergences are detected by ordinary tests, semantic CI, scientific CI and OAK?

Injected defects: unit mismatch, convention change, stale evidence, missing negative control, changed assumption, unsupported conclusion.

Metrics: detection rate, false-positive rate, time-to-detection and explanation quality.

## EXP-004 — Reuse-first vs generate-first

Question: does SEARCH → REUSE → ADAPT → GENERATE reduce duplication without degrading quality?

Metrics: duplicate semantic implementations, lines changed, test coverage, defects, latency, human review effort and maintainability proxies.

## EXP-005 — Tristan GitHub empirical case study

Question: how do capabilities, claims, evidence, PRs, negative memory and reusable components actually evolve across the repository history?

Analysis: temporal graph, capability genealogy, first reuse, duplicate emergence, M-minus propagation, crystallization rate and theory-code drift episodes.

Privacy/IP boundary: analyze only authorized repository material and preserve status/provenance. External publication remains separately reviewed.
