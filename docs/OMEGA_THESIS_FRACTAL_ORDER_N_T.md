# Ω-THESIS-FRACTAL-ORDER-N-T R0.1→R0.2

**Status:** C candidate extension of the existing `omega_thesis_factory_t`.  
**Doctrine:** reuse `ThesisSeed`, OAK status, Cognitive ISA `ZOOM/DEZOOM`, the canonical seed registry, and merged GO MAX / GO MIN. Do not create parallel memory, capability, or thesis ontologies.

## Mother law

A Tristan thesis is a zoomable research node in a sparse fractal forest:

```text
T^(0)
  --ZOOM--> T^(1)
  --ZOOM--> T^(2)
  ...
  --ZOOM--> T^(n)

T^(n)
  --DEZOOM RECEIPT--> ancestors
```

`n` is specialization depth only. It is never evidence strength, truth, novelty, maturity, or value.

## Stable address

```text
OMEGAT://OMEGA_THESIS_2N_GIT_T/TRANSFORM/FFWT/CONTINUOUS/STABILITY
```

The number of path segments is the fractal order.

## R0.1 — sparse ZOOM / DEZOOM kernel

Every child thesis candidate is encoded as the already-merged GO MAX / GO MIN vector.

Benefits:
- verified value
- evidence
- reuse
- reachability
- regenerability
- fertility

Costs/debts:
- execution cost
- structural debt
- proof debt
- semantic debt
- uncertainty
- irreversibility

The local planning proxy is the canonical `MaxMinVector.power_density()`.

ZOOM rules:

```text
candidate below local threshold -> reject
active child budget exhausted   -> HOLD
runtime max order reached       -> HOLD
selected child                  -> never exceeds parent OAK maturity
```

A ZOOM receipt explicitly states:

```text
oak_status_promoted = false
global_optimum_claimed = false
```

Logical order `n` is open. Runtime expansion is always bounded by policy and marginal value/cost.

DÉZOOM does not silently rewrite the parent thesis. A local result produces a review-only `DezoomReceipt` with a proposed action per ancestor:

```text
NO_CHANGE REVIEW UPDATE SUPPORT GENERALIZE REFUTE REOPEN
```

Permanent invariant:

```text
local result != global result
counterexample candidate != automatic ancestor refutation
supporting evidence != automatic OAK promotion
DEZOOM receipt != mutation authority
```

## R0.2 — canonical registry court

R0.2 connects the fractal forest to the existing `omega_thesis_factory_t.seed_registry` instead of inventing new thesis identities.

Current canonical registry:

```text
OMEGA_TRANSFORM_T
OMEGA_FCRYST_T
OMEGA_PREUVE_T
OMEGA_AUTO2_T
OMEGA_ENERGY_T
```

The compiler performs:

```text
canonical ThesisSeed registry
+ explicit normalized MaxMinVector per seed
-> seed_candidate
-> sparse ZOOM court
-> selected T^(1) children
-> source OAK maturity cap
-> RegistryZoomReceipt
```

### No inferred score

The registry supplies identity, axiom, CVCD invariants, OAK risks, code/Git/venture targets and M- memory. It does **not** supply a measured GO MAX/MIN score.

Therefore R0.2 enforces:

```text
missing MaxMinVector -> HOLD
prose length         != score
name prestige        != score
number of targets    != score
registry membership  != evidence
```

`score_inference_performed = false` is carried in the receipt.

### OAK maturity cap

A child can inherit a weaker source maturity but never a stronger one:

```text
child_status = min(parent_status, source_seed_status)
```

For example, an order-0 mother at status C cannot transform an `OMEGA_AUTO2_T` status-B seed into status C merely because ZOOM selected it.

### Sparse activation

All canonical seeds remain addressable, but only scored candidates enter the local court. GO MAX/MIN may then select fewer children than the number scored. This separates:

```text
exists in canon
!= scored now
!= selected now
!= scientifically validated
```

## Sparse ThesisForest

The canonical forest stores only the ZOOM parent relation. Higher graph layers may add Venn/shared-evidence/shared-code/cross-domain edges without changing thesis identity.

```text
ThesisSeed
  -> order-0 ThesisNode
  -> ranked ZoomCandidate set
  -> sparse order-(n+1) ThesisNode set
  -> experiments / proofs / evidence
  -> DezoomReceipt
  -> reviewed ancestor update
```

## Reuse map

R0.1→R0.2 deliberately reuses existing repository kernels:

- `omega_thesis_factory_t.core.ThesisSeed`
- `omega_thesis_factory_t.seed_registry.canonical_seeds`
- `omega_generative_closure_t.core.MaxMinVector`
- `omega_cognitive_computer_t` doctrine for `ZOOM/DEZOOM`
- OAK A-G maturity status from the existing thesis factory
- existing GitHub cumulative memory / lenses when repository history is needed

It does **not** recreate those systems.

## OAK non-claims

```text
order n != quality
order n != novelty
order n != evidence
power density != scientific truth
local ZOOM score != global optimum
registry membership != validation
missing score != low scientific value
selection != publication authority
DEZOOM suggestion != automatic mutation
many sub-theses != progress
long thesis != strong thesis
fractal naming != mathematical proof
```

## R0.2 acceptance surface

1. Existing canonical ThesisSeeds compile into candidate order-1 nodes.
2. No GO MAX/MIN score is inferred from prose or names.
3. Missing score vectors degrade to HOLD.
4. Selected children retain source seed axiom and OAK risks.
5. Child OAK maturity is capped by both parent and source seed.
6. Sparse active-child budget remains enforced.
7. Registry receipt preserves scored/held/selected provenance.
8. Deterministic tests qualify the branch before promotion.

## Next evidence frontier

R0.3 should attach measured evidence vectors to the five registry seeds, run matched baselines, record why branches survive or fail, then recurse inside selected seeds (for example TRANSFORM -> FFWT -> continuous/discrete -> stability/benchmark) without converting unmeasured fertility into evidence.
