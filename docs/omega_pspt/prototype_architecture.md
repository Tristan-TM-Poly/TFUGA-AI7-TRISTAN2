# Omega-PSPT++ Prototype Architecture

This document defines the executable architecture for turning Tristan solid-phase ideas into testable modules.

The guiding design is:

```text
geometry -> graph -> transport/spectrum -> CVCD descriptors -> Bayes-Tristan -> OAK decision
```

---

## 1. Module map

```text
sage_tristan/omega_pspt.py
  OAK levels
  claim-level discipline
  Bayes-Tristan posterior
  hyperloop score
  artifact penalty

sage_tristan/omega_pspt_geometry.py
  Cantor product supports
  Sierpinski carpet supports
  Menger sponge supports
  nearest-neighbor graph
  connected components
  cycle rank
  boundary descriptors

sage_tristan/omega_pspt_transport.py
  resistor-network adjacency
  weighted Laplacian
  dense small-network solver
  effective resistance
  ideal face-electrode supernodes
  normalized conductance descriptor

sage_tristan/omega_pspt_spectral.py
  graph spectral moments
  triangle and closed-walk descriptors
  compact tight-binding matrix
  Gershgorin spectral bounds
  inverse participation ratio
  CVCD-style spectral feature map
```

---

## 2. Data flow

### Step A — Generate geometry

```python
points = sierpinski_carpet_points(iteration=2)
edges = nearest_neighbor_edges(points)
summary = summarize_graph(points)
```

### Step B — Extract hyperloop invariants

```python
beta_1 = summary.cycle_rank
average_degree = summary.average_degree
boundary = summary.boundary_vertices
```

### Step C — Transport descriptor

```python
transport = summarize_transport(points, edges, axis=0)
score = normalized_conductance_score(
    transport,
    occupied_sites=len(points),
    bounding_size=3**2 * 3**2,
)
```

### Step D — Spectral descriptor

```python
spectral = spectral_summary(edges)
features = cvcd_spectral_features(spectral)
```

### Step E — OAK claim gate

```python
candidate.is_claim_allowed()
candidate.missing_for_promotion("OAK_6")
```

---

## 3. Why this is revolutionary but controlled

The architecture separates five layers that are often confused:

1. **Geometry**: holes, loops, fractal supports.
2. **Graph physics surrogate**: connectivity, effective resistance, spectral moments.
3. **Candidate physics**: localization, edge modes, topological markers, superconducting tests.
4. **Information compression**: CVCD features and cross-probe invariants.
5. **Claim governance**: OAK levels and negative-memory falsifiers.

This means a beautiful fractal cannot automatically become a claimed phase. It must pass through measurable descriptors and OAK filters.

---

## 4. Dependency strategy

### Current layer

The current layer is dependency-free and CI-friendly:

```text
Python standard library only
small lattices
fast unit tests
reproducible graph descriptors
```

### Next layer

Optional numerical extensions can add:

```text
NumPy for dense eigensolvers
SciPy for sparse Laplacian and Hamiltonian solvers
NetworkX for graph algorithms
Matplotlib for plots
pandas for experiment tables
```

The dependency-free core should remain as the stable OAK scaffold.

---

## 5. Prototype milestones

### Milestone P0 — Canon layer

- definitions;
- phase table;
- OAK protocols;
- roadmap;
- experiment cards.

### Milestone P1 — Geometry engine

- Cantor/Sierpinski/Menger supports;
- graph summaries;
- hyperloop/cycle rank;
- boundary descriptors.

### Milestone P2 — Transport engine

- effective resistance;
- face-electrode contact model;
- normalized conductance;
- matched-control comparison.

### Milestone P3 — Spectral engine

- spectral moments;
- simple tight-binding matrix;
- IPR;
- CVCD-style compact descriptors.

### Milestone P4 — Active OAK engine

- phase-card loader;
- next-test recommender;
- negative-memory artifact gate;
- report generator.

### Milestone P5 — Scientific demos

- fractal vs random porous control;
- hyperloop resonance surrogate;
- topology toy model;
- Omega-TFTS candidate simulation sequence.

---

## 6. Minimal demo target

A first complete demo should output a table like:

```text
geometry | n | sites | edges | beta_1 | R_eff | G_norm | trace_A2 | trace_A4 | OAK_status
```

This table is the first bridge between Tristan geometry and falsifiable material hypotheses.

---

## 7. OAK stop rules

A result must be downgraded if:

- the effect disappears under matched porosity;
- the effect disappears with contact normalization;
- random controls perform equally;
- the spectral descriptor does not distinguish controls;
- CVCD features are not stable under noise;
- the candidate resembles a known negative-memory artifact.

---

## 8. Canonical prototype equation

```text
Phi_candidate = OAK(BayesT(CVCD(Transport(Spectral(Graph(Geometry))))))
```

Expanded:

```text
Lambda_n -> (V,E) -> {beta_1, boundary, R_eff, spectral_moments}
         -> CVCD features -> posterior -> OAK promotion/demotion
```
