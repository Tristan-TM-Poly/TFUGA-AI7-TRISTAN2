# Capability OS Virtual Tristan — Minimum Sufficient Swarm R0.2

## Goal

Reduce a READY Virtual Tristan population to the smallest supplied finite subset that still satisfies frozen residual coverage, verified-output coverage, and minimum evidence constraints.

## Pipeline

`VirtualTristanPopulation -> SwarmProbeResult -> MarginalContribution -> Exhaustive finite ablation -> MinimumSufficientSwarmReport`

## Semantics

For each Virtual Tristan `v`, marginal contribution is computed by removing `v` from the full supplied population and measuring the loss in residual coverage, verified outputs, and minimum evidence score.

The minimum sufficient swarm searches subsets in increasing cardinality. The first cardinality with a feasible subset is minimal over the supplied finite population. Within that cardinality, lower supplied cost wins; remaining ties are stable by identity.

## OAK laws

- `MoreTristans != MoreIntelligence`
- `MarginalContribution != CausalContribution`
- `MinimumSuppliedSubset != UniversalMinimum`
- `AblationPASS != ExternalSuccess`
- `RoleIdentity != IndependentEvidenceSource`
- `Removed != UselessEverywhere`
- `MINIMAL != PermissionToExecute`

## Fail-closed conditions

The court returns `HOLD` if the source population is not READY, any population member lacks a probe result, unknown members appear in the probe set, or no supplied subset satisfies the frozen requirements.

## Anti-inflation

R0.2 adds no new agent ontology, authority system, memory system, or scheduler. It consumes R0.1 Virtual Tristan populations and Capability OS contracts.

## Next falsification

The next useful test is empirical: run the same bounded task with the full swarm and with the selected minimum swarm, freeze criteria before execution, and compare repair iterations, CI failures, tool calls, residuals, and time-to-GlobalPASS. A structurally minimal swarm is not yet an operationally superior swarm.
