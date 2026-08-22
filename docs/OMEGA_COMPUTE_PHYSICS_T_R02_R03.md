# Ω-COMPUTE-PHYSICS-T∞ / Ω-COMPLEXITY-ATLAS-T∞ — R0.2–R0.3

## Status

**Executable OAK-safe prototype.** R0.2 adds predictive validation, calibrated empirical uncertainty, drift evidence and `Complexity Diff`. R0.3 adds bounded active benchmarking and finite-domain inverse resource design.

The epistemic boundary remains strict:

```text
measured scaling / fitted law / held-out validation / conformal interval
!=
mathematical proof of asymptotic Big-O or Theta
```

Likewise:

```text
regime break != proof of cache/NUMA/GPU causality
active-learning score != exact expected information gain
best finite candidate != global optimum outside the tested domain
```

---

## 1. R0.2 — from fit quality to predictive evidence

R0.1 could fit a multivariate resource surface. R0.2 asks the harder question:

> Does the discovered law predict measurements that were not used to select it?

The R0.2 pipeline is:

```text
ResourceSamples
    -> deterministic development/calibration split
    -> candidate model families
    -> K-fold predictive comparison on development data
    -> model selection
    -> untouched calibration set
    -> split-conformal residual radius
    -> validated empirical certificate
```

### Candidate families

`validation.py` exposes bounded `ModelCandidate` objects. The default library includes:

- linear;
- linear + `log(x)` + `x log(x)`;
- quadratic;
- quadratic + logarithmic terms;
- cubic.

This is deliberately bounded. It is not an unconstrained symbolic-regression search.

### Selection criteria

The primary criterion is held-out cross-validation RMSE:

```text
cv_rmse
```

R0.2 also records heuristic information criteria:

```text
aic_proxy
bic_proxy
mdl_proxy
```

They are explicitly named `proxy` because ridge-regularized feature models do not satisfy all assumptions required to interpret textbook AIC/BIC as exact likelihood criteria.

---

## 2. Independent calibration and uncertainty

Model selection and uncertainty calibration must not reuse the same evidence carelessly.

R0.2 reserves a calibration partition that is not used to choose the model family. For calibration residuals

```text
r_i = |y_i - y_hat_i|
```

it forms a split-conformal symmetric radius `q` and reports

```text
[y_hat - q, y_hat + q]
```

with the configured miscoverage level `alpha`.

This is a finite-domain predictive interval under the usual exchangeability assumptions. It is not a guarantee after software, hardware, workload or distribution drift.

The validation certificate records:

```text
selected_candidate
selection_criterion
n_total
n_development
n_calibration
K folds
candidate scores
calibration RMSE
calibration MAE
calibration R²
conformal alpha
conformal radius
calibration coverage
OAK warning
```

---

## 3. Drift Sentinel

Once a law is deployed, every new benchmark becomes a falsification opportunity.

For recent samples the sentinel computes relative predictive errors and reports:

```text
median relative error
P95 relative error
fraction above configured tolerance
optional conformal interval miss rate
```

A drift flag means only:

> the empirical law no longer matches recent measurements within the configured tolerance.

It does **not** identify the cause. Possible causes include:

- algorithm changes;
- compiler/runtime changes;
- cache or NUMA behavior;
- thermal throttling;
- contention;
- different data morphology;
- measurement noise;
- instrumentation changes.

Causal diagnosis is a later experimental layer.

---

## 4. Complexity Diff

A point benchmark can hide scaling regressions. R0.2 therefore compares two complete empirical laws over an explicit evaluation set.

For every point `x`:

```text
Delta_R(x) = R_new(x) - R_old(x)
relative_Delta_R(x) = Delta_R(x) / |R_old(x)|
```

The diff reports:

- mean and median relative change;
- largest predicted increase/decrease;
- regression/improvement/neutral fractions;
- overlap of certified model domains;
- local elasticity change at an anchor point;
- empirical 1-D crossover candidates;
- optional per-point deltas.

For a time resource, `lower-is-better` means positive relative change is classified as regression. For quality metrics, callers can use `higher-is-better`.

### Local scaling change

At an anchor `x`, each model receives the local elasticity

```text
kappa_i = d log R / d log x_i
```

and `Complexity Diff` reports

```text
Delta_kappa_i = kappa_i,new - kappa_i,old
```

This can detect an empirical scaling-shape change even when a single benchmark remains fast.

Again:

```text
Delta_kappa != proof that asymptotic complexity changed
```

A genuine asymptotic promotion belongs to the Complexity Proof Ladder.

---

## 5. Machine-readable R0.2 evidence

R0.2 adds:

```text
complexity_atlas/evidence_schema_v0_2.json
```

with portable evidence kinds:

```text
validated-resource-model
complexity-diff
drift-report
```

CLI:

```bash
python -m omega_compute_physics_t.r02_cli validate samples.jsonl \
  --target wall_time_s

python -m omega_compute_physics_t.r02_cli diff old_atlas.json new_atlas.json \
  --target wall_time_s \
  --variable n \
  --start 10 \
  --stop 100000

python -m omega_compute_physics_t.r02_cli drift atlas.json recent.jsonl \
  --target wall_time_s \
  --fail-on-drift
```

The CLI is designed so GitHub Actions, agents and external tooling can consume evidence without importing internal Python objects.

---

# R0.3 — Active Benchmarking

## 6. The combinatorial problem

For `d` variables and `m` levels each, a Cartesian campaign contains

```text
m^d
```

experiments.

Blind grid search rapidly becomes wasteful. R0.3 makes benchmark selection an explicit bounded decision problem.

---

## 7. Bounded geometric design spaces

`geometric_design_space` constructs positive logarithmic candidate grids from bounds:

```python
{
    "a": (a_min, a_max),
    "b": (b_min, b_max),
}
```

A hard `max_points` gate prevents accidental experiment explosion.

This is a candidate generator, not yet a universal experimental-design engine.

---

## 8. Information proxy

For several plausible empirical models evaluated at candidate `x`, R0.3 computes model disagreement plus geometric novelty relative to existing measurements.

Conceptually:

```text
I_proxy(x)
  = w_D * disagreement(x)
  + w_N * novelty(x)
```

If a cost model is available:

```text
score(x) = I_proxy(x) / predicted_cost(x)^p
```

This realizes the principle:

```text
useful uncertainty reduction per resource unit
```

but the implementation calls this `information_proxy`, not exact information gain.

### Discriminating experiment

Given two competing empirical laws, `discriminating_experiment` selects the bounded candidate where their predictions disagree most strongly per predicted cost.

This directly supports OAK falsification campaigns:

```text
H1 vs H2
    -> choose discriminating x
    -> measure
    -> update evidence
```

---

## 9. Diverse active batches

`select_next_experiments` can choose more than one candidate while applying a minimum log-coordinate separation.

This prevents a top-k planner from spending an entire batch on nearly identical points.

The current diversity gate is geometric and deterministic. Future versions can use D-optimality, Bayesian design, mutual-information estimators or Gaussian-process acquisition functions behind the same OAK contract.

---

# R0.3 — Budget Compiler

## 10. Inverting the Atlas

Forward question:

```text
configuration x -> predicted resources
```

Inverse question:

```text
resource constraints -> best feasible configuration x*
```

R0.3 implements the second question over an explicit bounded candidate set.

Example constraints:

```text
wall_time_s <= 60
memory_mb <= 16000
quality >= 0.95
```

Optional uncertainty radii make feasibility robust:

```text
predicted upper resource <= budget
```

rather than trusting the point estimate alone.

---

## 11. ResourceConstraint

A constraint can define:

```text
upper bound
lower bound
safety margin
```

For predicted interval `[low, high]`:

- an upper-bound resource must satisfy robust `high <= allowed`;
- a lower-bound quality must satisfy robust `low >= allowed`.

Thus a configuration whose point prediction barely fits but whose uncertainty crosses the budget is rejected.

---

## 12. Finite-domain optimum

`compile_budget` evaluates supplied candidates, removes infeasible configurations and selects the best remaining candidate according to an explicit objective:

```text
minimize wall_time
maximize quality
minimize monetary_cost
...
```

The certificate says **finite-domain empirical inverse design**.

It never says global optimum unless the complete feasible mathematical domain has actually been searched/proved.

---

## 13. Pareto Atlas

For multiple competing objectives there may be no single best solution.

R0.3 therefore computes the nondominated finite candidate set:

```text
ParetoFront(time, memory, energy, cost, quality, ...)
```

A candidate is excluded when another candidate is no worse on every requested objective and strictly better on at least one.

This gives the Atlas a multi-resource decision surface rather than forcing all resources into one arbitrary scalar.

A separate `quality_per_cost` helper exists only when a scalar ranking is explicitly desired.

---

## 14. R0.1 -> R0.3 architecture

```text
SOURCE / PIPELINE
    |
    v
Profiler
    |
    v
ResourceSample(x, R, provenance)
    |
    +------------------------------+
    |                              |
    v                              v
Empirical law discovery       Resource hypergraph
    |
    v
R0.2 predictive validation
    |
    +--> conformal uncertainty
    +--> drift sentinel
    +--> Complexity Diff
    |
    v
R0.3 active benchmark planner
    |
    +--> discriminating experiments
    +--> cost-aware experiment ranking
    |
    v
R0.3 inverse resource design
    |
    +--> robust constraints
    +--> finite optimum
    +--> Pareto front
    v
OAK evidence packet
```

---

## 15. Tests added

R0.2 tests cover:

- held-out calibration partition;
- conformal interval construction;
- predictive candidate selection;
- drift under persistent resource shift;
- uniform resource improvement diff;
- preserved local exponent under constant-factor improvement;
- sampled crossover detection;
- serialized empirical-model reconstruction.

R0.3 tests cover:

- bounded geometric design generation;
- model-disagreement experiment selection;
- novelty/diversity active batching;
- robust budget feasibility with uncertainty radius;
- quality-maximizing feasible selection;
- Pareto elimination of dominated configurations;
- explicit quality-per-cost scalarization.

The repository Reactor audit executes these with the full repository test suite.

---

## 16. OAK Proof Ladder

The branch uses the following distinction:

```text
L0  intuition
L1  in-sample empirical fit
L2  held-out predictive validation
L3  replicated multi-machine / multi-environment evidence
L4  algorithmic explanation
L5  mathematical bound
L6  formal proof
```

R0.2 strengthens the implementation primarily from L1 toward L2.

Neither R0.2 nor R0.3 automatically promotes an empirical law to L5/L6.

---

## 17. M- / negative-memory rules

Record these failure modes permanently:

1. **Training fit masquerading as prediction**  
   Fix: held-out evidence.

2. **Finite exponent masquerading as Big-O proof**  
   Fix: empirical/proof namespaces remain distinct.

3. **Calibration data reused for model shopping**  
   Fix: development/calibration separation.

4. **Crossover interpreted as hardware causality**  
   Fix: label crossover as empirical candidate until intervention/profiling supports cause.

5. **Active score called exact information gain**  
   Fix: `information_proxy` nomenclature.

6. **Grid optimum called global optimum**  
   Fix: finite-domain certificate.

7. **Uncertainty ignored near a hard resource boundary**  
   Fix: robust budget intervals and safety margins.

8. **Benchmark explosion**  
   Fix: candidate caps and active selection.

---

## 18. Next promoted frontier — R0.4

R0.4 should be attempted only after preserving the R0.1–R0.3 green baseline.

Priority components:

### MachineGenome-T

Calibrated, provenance-rich effective machine fingerprint:

```text
CPU/runtime identity
core count
memory hierarchy metadata where available
measured scalar throughput
measured memory-copy throughput
thread scaling curves
GPU adapter plugins when explicitly available
software/compiler/runtime versions
```

The word **measured** is essential. Advertised peak FLOPs alone are not sufficient.

### Complexity-IR

Hardware-independent workload representation such as:

```text
LOAD
STORE
ALLOC
MATMUL
REDUCE
BRANCH
TRANSFER
SYNC
SERIALIZE
NETWORK
```

with symbolic/empirical volumes attached.

### Cross-hardware translation

Only after MachineGenome calibration:

```text
WorkloadGenome x MachineGenome -> predicted resources + uncertainty
```

Cross-machine predictions must be held out and calibrated before promotion.

### DAG pipeline composition

Replace the R0.1 sequential pipeline approximation with:

```text
critical path
resource overlap
contention
buffer lifetime
transfer edges
synchronization
```

### PhaseMap R0.4

Upgrade empirical slope-break candidates into tested hypotheses by correlating with independent counters such as cache misses, RSS/VRAM pressure, device transfers or synchronization traces.

---

## 19. Canonical summary

R0.1 answered:

> What resource surface did we measure?

R0.2 answers:

> Does the law predict held-out measurements, how uncertain is it, did it drift, and how did it change between versions?

R0.3 answers:

> Which experiment should we measure next, and which configuration best satisfies our bounded resource constraints?

The resulting loop is:

```text
measure
-> fit
-> validate
-> quantify uncertainty
-> falsify/drift-check
-> compare versions
-> choose next experiment
-> invert under resource budgets
-> measure again
```

This is the first executable closed loop of Ω-COMPUTE-PHYSICS-T∞.
