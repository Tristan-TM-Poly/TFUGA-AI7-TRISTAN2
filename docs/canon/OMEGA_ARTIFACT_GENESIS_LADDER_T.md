# Ω-ARTIFACT-GENESIS-LADDER-T

The ladder is a governed artifact-expansion method, not a requirement to maximize file count.

For level n, target coverage is `2^n` artifact classes. The next level `n+1` must always be probed before saturation is claimed. The probe may materialize only the missing high-value surfaces when the remaining slots are virtual/regenerable projections.

Define marginal verified gain:

`MVG_n = (VerifiedCapability_{n+1} - VerifiedCapability_n) / (Complexity + Debt + Compute + ReviewCost)`.

Stop condition candidate: `MVG_n <= epsilon` with all hard invariants preserved and no unresolved high-value residual. This is a heuristic until benchmarked.

Hard gates: provenance, reversibility, permission, evidence type, exact-head CI, no unresolved blocking review residue, and `LocalPASS != GlobalPASS`.

The 16 canonical artifact classes are: claim, derivation, schema, code, tests, benchmark, data/figure, document, example, CLI/API, CI, provenance, OAK receipt, negative-memory case, integration bridge, regeneration manifest.
