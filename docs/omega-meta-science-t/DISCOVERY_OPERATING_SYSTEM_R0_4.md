# Ω-DISCOVERY-OPERATING-SYSTEM-T∞² R0.4

**Status:** executable research prototype / deterministic contract layer / OAK-bounded.

R0.4 does not add another independent meta-science branch. It turns the R0.1-R0.3 stack into a small operating-system layer that can reject invalid scientific type promotions, explain semantic changes between theory versions, rebuild only affected descendants in a scientific dependency graph, attach machine-readable evidence/tests to claims, and compare candidate discovery programs with bounded internal metrics.

## Mother pipeline

```text
Scientific IR / Discovery ABI
    -> typed claim contract
    -> semantic theory diff
    -> scientific build graph
    -> proof-carrying claim
    -> OAK gate
    -> VDU + Discovery ROI
    -> next bounded action
```

The operating law is:

```text
compile broadly -> type-check strictly -> diff semantically
-> invalidate transitively -> certify claims -> value only after OAK
```

## 1. Epistemic type checker

`check_claim_type()` implements a deliberately small fail-closed claim type system.

Supported target classes include observation, correlation, causal, simulation, experimental, theorem, conjecture, hypothesis and supported.

The R0.4 contract refuses several invalid implicit conversions: correlation to causal without a declared `causal_design`; claim to theorem without `formal_proof`; claim to experimental without `experiment`; and claim to supported without declared reproducible evidence.

These rules are software contracts, not a complete epistemology. A `causal_design` label is a declared evidence type and is not itself proof that a real experiment establishes causality.

## 2. Theory semantic diff

`theory_diff()` compares two `TheorySnapshot` objects with the same `theory_id` and separates assumptions, laws, evidence, representations and domain changes. This is the seed of Scientific Git:

```text
file diff -> semantic theory diff -> claim impact -> selective rebuild
```

R0.4 does not infer semantic equivalence from arbitrary source code or natural-language documents. The snapshots are explicit declarations.

## 3. Scientific build graph

`ScientificBuildGraph` represents dependency chains such as:

```text
instrument -> dataset -> model -> claim -> artifact
```

`audit()` checks duplicate identifiers, missing dependencies and cycles. `invalidated_by()` computes transitive descendants that must be rebuilt when declared upstream nodes change.

Canonical fixture:

```text
change(dataset) -> invalidate(dataset, model, claim, artifact)
```

This is the seed of `science build`, `science diff` and `science reproduce`, without claiming automatic reproducibility of an external workflow.

## 4. Proof-carrying claims

`ClaimCertificate` bundles the claim, requested target type, OAK status, tests passed and reviewed counterevidence. `validate_claim_certificate()` fails closed if the epistemic type contract fails, OAK is not `PASS`, or no tests are attached. Unreviewed declared counterevidence is surfaced as a warning.

The certificate proves only that the supplied machine-readable contract passed the declared gates, not that the scientific statement is externally true.

## 5. Verified Discovery Unit

`verified_discovery_unit()` replaces unsupported head-count productivity claims with a bounded internal metric:

\[
VDU = 0.30 U + 0.25 R + 0.20 G + 0.15 A + 0.10 N
\]

where `U` is uncertainty reduction, `R` reproducibility, `G` generalization, `A` artifact maturity and `N` novelty evidence. If `oak_pass=False`, the VDU score is exactly zero.

The weights are policy choices, not natural constants.

## 6. Discovery ROI

`discovery_roi()` computes:

\[
ROI_D = \frac{V_{expected} P_{validation}}{C_{compute}+C_{experiment}+C_{human}+C_{risk}}.
\]

All inputs are supplied assumptions. The output is not a company valuation, revenue forecast or guarantee; it is a transparent ranking primitive.

## 7. Deterministic replay

```bash
python -m omega_meta_science_t.operating_system_cli
python -m omega_meta_science_t.operating_system_cli --compact
```

Tests:

```bash
python -m pytest -q \
  tests/test_omega_meta_science_t.py \
  tests/test_omega_meta_science_discovery.py \
  tests/test_omega_meta_science_geometry.py \
  tests/test_omega_meta_science_operating_system.py
```

The package remains standard-library only.

## 8. Acceptance fixtures

CI checks that correlation cannot become causal without a declared causal-design record; the promotion is accepted when that record exists; theory diffs separate change classes; invalidation is transitive; cycles are rejected; proof-carrying claims fail closed without tests; VDU is bounded and zeroed by OAK failure; Discovery ROI replays exactly; and the composed R0.4 report preserves the invariants.

## 9. OAK boundaries

R0.4 does **not** establish a universal scientific type theory, causal truth from an evidence label, theoremhood from an unverified string labelled `formal_proof`, semantic equivalence of arbitrary theories, reproducibility of external instruments or datasets, universal units of scientific productivity, monetary valuation of the architecture, autonomous scientific authority, or historical novelty/priority of individual primitives.

## 10. R0.5 promotion path

R0.5 should add hash-addressed real artifacts, provenance-derived evidence dependency graphs, optional SAT/SMT claim checking, active experiment portfolios, semantic lineage/bisect, calibrated VDU histories, held-out Discovery ROI validation, GreatSages transformation provenance and an OAKGate/Asset Factory handoff only after scientific contract PASS.

```text
plus ultra = more executable, more falsifiable, more attributable,
and more comparable under explicit budgets — not merely more named modules.
```
