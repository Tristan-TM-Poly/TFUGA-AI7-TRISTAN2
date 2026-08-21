# Ω Artifact Genesis Ladder — 2^n → n+1

## Mission
Expand a project through power-of-two artifact coverage, then always execute one additional `n+1` probe before claiming saturation.

## Loop
1. Inventory existing artifacts and gates.
2. Choose smallest useful level `n`.
3. Materialize up to `2^n` artifact surfaces across theory, code, tests, schemas, examples, benchmarks, docs, CI, provenance and OAK.
4. Run exact-head qualification.
5. Execute the `n+1` probe: add or simulate the next power-of-two coverage level and measure marginal verified gain.
6. Stop only when marginal verified gain is negligible relative to complexity/debt, or when a hard gate blocks expansion.
7. Merge only an exact qualified head; never equate generation with truth or authority.

## Required laws
`Generated != Proven`
`MoreArtifacts != MoreValue`
`2^nCoverage != SaturationProof`
`n+1Probe != AutomaticPromotion`
`CI_PASS != ExternalTruth`
`Recommendation != Authority`

## Artifact classes
Claim, derivation, schema, code, tests, benchmark, figure/data, document, example, CLI/API, CI, provenance, OAK receipt, negative-memory case, integration bridge, regeneration manifest.

## Merge protocol
Fresh main -> branch -> materialize -> tests/OAK -> inspect exact-head CI -> review residue -> compare `behind=0` -> ready -> merge with expected head SHA. If any gate fails: HOLD/repair/requalify.
