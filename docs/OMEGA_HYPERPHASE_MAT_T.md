# Ω-HYPERPHASE-MAT-T∞ — Thermodynamique hypergraphique multi-échelle de la matière réelle

**Status:** R1 executable research scaffold — OAK-safe.  
**Scope:** finite exact reference models, phase/transition evidence representation, falsifiable hypotheses.  
**Non-claim:** this document does **not** assert that matter is literally a hypergraph and does not establish a new thermodynamic law.

## 1. Mother model

Represent a material state at a selected resolution by

\[
\mathfrak M=(X,\mathcal H,\Theta,\mathcal E),
\]

where `X` are physical degrees of freedom, `H` is an explicit representation of effective interactions/organization, `Θ` contains control parameters, and `E` specifies the energy model. A hyperedge `e={i1,...,ik}` carries a many-body term

\[
E(X,\mathcal H)=\sum_i \epsilon_i(X_i)+\sum_{e\in\mathcal H}\Phi_e(X_e).
\]

The R1 executable uses Ising-like variables only because exact enumeration supplies a transparent truth model. It is a benchmark nucleus, not a claim that real materials reduce to Ising spins.

## 2. Fixed and dynamic topology

For fixed `H`:

\[
Z_{\mathcal H}=\sum_X e^{-\beta E(X,\mathcal H)}.
\]

For an explicitly declared finite set of annealed interaction topologies:

\[
Z_{HG}=\sum_{\mathcal H}\sum_X e^{-\beta E(X,\mathcal H)}.
\]

`structural_energy` can encode a model cost for an admissible topology. It is not silently interpreted as a new fundamental chemical potential.

## 3. Entropy without inventing a new thermodynamic law

Given the normalized joint distribution `P(X,H)`, R1 audits

\[
S(X,\mathcal H)=S(\mathcal H)+\mathbb E_{\mathcal H}[S(X\mid\mathcal H)].
\]

The package reports total entropy, topology entropy, conditional configuration entropy and the numerical chain-rule residual. `S(H)` is meaningful only relative to the declared ensemble of admissible interaction topologies.

## 4. Observables and response functions

R1 computes exactly for the finite model:

- `log Z`, `F=-k_B T log Z`, `U`, `S`;
- heat capacity from energy fluctuations;
- signed and absolute magnetization;
- magnetic-style susceptibility from finite fluctuations;
- hypergraph-state probabilities and mean active hyperedge count;
- arbitrary observable expectations and covariances.

The observable/covariance surface is the intended bridge to FFWT-HAC-CVCD: real descriptors can later replace the toy spin observables while preserving an auditable fluctuation/correlation layer.

## 5. Phase tensor / phase fingerprint

A future real-material phase fingerprint should be an explicitly versioned vector/tensor of measured or simulated observables, for example

\[
Q=(\rho,M,P,Q_{nem},\epsilon,\Psi_{cryst},n_{def},A_{interface},C_2,C_3,\ldots).
\]

Possible additions include XRD, Raman, EIS, calorimetry, elastic response, defect/interface statistics, hyperedge-order statistics and multi-scale FFWT/CVCD descriptors. The inclusion of a descriptor is a model choice and must be benchmarked against simpler baselines.

## 6. Phase Hypergraph Atlas

`PhaseHypergraphAtlas` makes phase knowledge machine-readable:

- phase nodes carry order parameters and evidence status;
- transition hyperedges can connect one or several source/target phases;
- transition records carry mechanism and control parameters;
- references to nonexistent phases are rejected.

This atlas is an evidence/data structure. It does not turn a suggested transition into a physical fact.

## 7. Criticality and finite-size OAK gate

Exact enumeration of a finite system has analytic finite partition sums at positive temperature. Therefore an R1 response maximum is labelled

`FINITE_SIZE_CROSSOVER`

and **never** promoted automatically to a thermodynamic phase transition. A bulk transition requires a thermodynamic-limit argument, finite-size scaling, independent simulation/experiment, or another appropriate physical proof.

A later R2 may compare conventional thermodynamic stability modes (e.g. Hessian eigenvalues) with graph/hypergraph spectral modes. The proposed correspondence is a **hypothesis to benchmark**, not an identity.

## 8. Real-matter mapping

The same schema can represent multiple resolutions without forcing identical nodes at every scale:

`electronic/orbital -> atom -> local motif -> unit cell -> defect/interface -> grain -> voxel -> component`.

Coarse-graining must declare what is integrated out, which observables are preserved, and the residual/error introduced. Nested HGFM objects are a representation strategy, not permission to ignore conservation laws or known constitutive physics.

## 9. OAK epistemic ladder

R1 uses these statuses:

- `ESTABLISHED`: standard mathematical/statistical identity or finite-size guardrail;
- `DEFINITION`: semantics chosen by this project;
- `MODEL`: executable construction whose consequences follow from declared assumptions;
- `HYPOTHESIS`: empirical/generalization claim requiring comparison and falsification;
- `CONJECTURE`: reserved for stronger unsupported propositions.

`omega_hyperphase_mat_t.claims.CLAIMS` stores the initial machine-readable claim/falsifier registry.

## 10. Falsification program

Promote the real-material program only if it beats declared baselines. Minimum OAKBench families:

1. **pair-only vs k-body:** do higher-order descriptors improve held-out prediction enough to justify complexity?
2. **fixed vs dynamic H:** does annealed/reconfigurable topology improve calibrated likelihood or observables rather than merely overfit?
3. **conventional vs hypergraph criticality:** does an HG spectral signal add predictive lead time over heat capacity, susceptibility and standard structural descriptors?
4. **single-scale vs multi-scale:** do HGFM/FFWT features improve phase classification or transition forecasting under distribution shift?
5. **ablation:** remove defects, interfaces, topology descriptors and higher-order edges one family at a time.
6. **negative controls:** randomized hyperedges and label-shuffled data must not retain claimed predictive gains.

## 11. Executable quick start

```bash
python -m omega_hyperphase_mat_t --t-min 0.5 --t-max 5 --steps 16
python -m omega_hyperphase_mat_t --claims
pytest -q tests/test_omega_hyperphase_mat_t.py
```

The demo contains four sites, pair interactions and an optional collective four-body hyperedge. It emits a temperature sweep, entropy decomposition and finite-size crossover marker.

## 12. R2–R5 roadmap

- **R2 — real descriptors:** phase fingerprints, units/provenance schemas, defect/interface objects, Hessian and hypergraph Laplacian diagnostics.
- **R3 — multiscale:** HGFM Zoom, coarse-graining contracts, FFWT-HAC-CVCD correlation signatures and reconstruction residuals.
- **R4 — material adapters:** ingest public DFT/MD/MC/experimental phase data; Bayes-Tristan posteriors over phase/topology hypotheses.
- **R5 — inverse design:** property target -> phase fingerprint -> interaction/topology target -> candidate structure/process, with OAK feasibility and uncertainty gates.

## 13. Canonical distinction

> Hypergraph = explicit model of relationships/interactions/organization.  
> Thermodynamics = physical/statistical constraints applied to declared degrees of freedom.  
> A useful hypergraph descriptor is not automatically a new thermodynamic state variable.  
> A finite peak is not automatically a bulk phase transition.

This distinction is the R1 anti-bullshit invariant.
