# Ω-SOLID-T∞ R0.1

## Executable theory of solids, material genomes, hypergraphs and OAK validation

Ω-SOLID-T∞ turns the conceptual theory of all solids into a dependency-free Python research kernel. It is not a database claiming to enumerate every material. It is a generative representation able to encode known solids, hypothetical designs, processes, defects, interfaces, properties, evidence and uncertainty in one auditable object.

The package is deliberately conservative about scientific status:

- established equations remain identified as established approximations;
- illustrative archetype numbers are not certified datasets;
- simulated values remain simulated;
- proposed architectures remain proposed;
- hypergraph or CVCD scores are engineering descriptors, not new physical laws;
- fabrication and safety claims require experiments and professional review.

---

## 1. Central object: `SolidGenome`

A material is not uniquely identified by composition. Two specimens with the same nominal formula can differ because of grain size, phase fraction, defects, porosity, texture, interfaces, processing route, residual stress, ageing and environment.

`SolidGenome` therefore records:

1. identity and material family;
2. composition and fraction basis;
3. a normalized bond-mixture vector;
4. order class and dimensionality;
5. phases and phase fractions;
6. defects with criticality and function;
7. interfaces as explicit material objects;
8. measured, simulated or proposed properties;
9. geometry and hierarchy;
10. manufacturing process and history;
11. applied fields and environment;
12. applications and risks;
13. assumptions, provenance and next experiments;
14. epistemic status.

The serializer is deterministic and produces a SHA-256 fingerprint that excludes only the creation timestamp. A change in composition, process, defect state, evidence or risk therefore changes the fingerprint.

### Invariants enforced at construction

- composition fractions sum to one within tolerance;
- phase fractions sum to one when phases are present;
- bond weights sum to one when bond contributions are present;
- property names are unique;
- defect criticality lies in `[0, 1]`;
- phase fractions and porosity remain physical;
- quantities retain units and optional uncertainty.

These checks are not a replacement for dimensional analysis or a mature units package. They prevent silent metadata loss and obvious structural inconsistencies.

---

## 2. Twelve archetypes

The MVP contains twelve deliberately different solids. They are test fixtures and ontology stress cases, not authoritative property records.

| Key | Structural purpose |
|---|---|
| `metallic_crystal` | metallic bonding, dislocations, vacancies, conduction |
| `ionic_crystal` | ionic crystal, point defects and brittle flaws |
| `covalent_network` | strong covalent network and defect centers |
| `semiconductor_crystal` | dopant, electronic trap and interface |
| `amorphous_glass` | frozen disorder, fictive history and surface flaws |
| `amorphous_polymer` | rate-dependent chain network and ageing |
| `semicrystalline_polymer` | crystalline/amorphous coexistence and interphase |
| `fiber_composite` | anisotropy, interphase and delamination |
| `porous_ceramic` | pore topology, transport and brittle failure |
| `granular_solid` | jammed contact network and force-chain heterogeneity |
| `two_dimensional_material` | effective 2D confinement and substrate interface |
| `architected_lattice` | hierarchical geometry and proposed fractal-mycelial design |

Each archetype can be emitted as JSON, analyzed through OAK and converted to a hypergraph bundle.

```bash
omega-solids list-archetypes
omega-solids emit-archetypes --output-dir generated/omega_solids/archetypes
omega-solids atlas --output-dir generated/omega_solids/atlas
```

---

## 3. `SolidHyperGraph`

The hypergraph represents collective relationships that pairwise graphs often flatten incorrectly.

### Node classes

- solid/system;
- composition component;
- phase;
- defect;
- interface;
- observable property;
- process step.

### Hyperedge classes

- `constitutes` links a solid and all composition components;
- `phase_coexistence` links a solid and coexisting phases;
- `defect_context` links a defect, solid and relevant phase;
- `interface_coupling` links an interface and adjacent phases;
- `emergent_property` links an observable to the solid, phases and defects;
- `process_transition` links manufacturing steps in order;
- `produces` links the final process step to the resulting solid.

The implementation supports:

- deterministic node and edge order;
- incidence indexing;
- neighbors and incident hyperedges;
- connected components;
- shortest projected hyperpaths;
- integrity checks;
- JSON serialization;
- GraphML projection through explicit hyperedge nodes.

GraphML does not natively preserve general hyperedges. Ω-SOLID-T∞ therefore represents each hyperedge as a node connected to its members. This avoids falsely treating a multi-body relationship as a set of independent physical bonds.

---

## 4. CVCD-Solid signature

The current executable signature is a compact comparison vector, not a proof of equivalence. It contains:

- normalized composition entropy;
- bond hybridization entropy;
- phase entropy;
- aggregate defect criticality;
- interface complexity;
- porosity;
- hierarchy depth;
- property-tensor anisotropy;
- provenance coverage;
- uncertainty coverage;
- measured-property fraction;
- counts of properties, defects, interfaces and phases.

```python
from omega_solids_t.atlas import build_archetype
from omega_solids_t.invariants import build_signature, signature_distance

metal = build_archetype("metallic_crystal")
ceramic = build_archetype("porous_ceramic")

a = build_signature(metal)
b = build_signature(ceramic)
print(signature_distance(a, b))
```

The distance is a descriptor-space distance. It must not be interpreted as a universal physical distance between materials. Weights must be selected for a defined task and validated against downstream outcomes.

---

## 5. DefectTensor-T

Defects are represented as functional operators rather than only imperfections. A defect record can contain:

- kind;
- density and unit;
- geometry;
- orientation;
- mobility;
- formation energy;
- criticality;
- physical or functional role;
- epistemic status.

`DefectInteractionGraph.infer` generates explicitly labeled heuristic candidate interactions. Examples include:

- crack–pore stress-concentration coalescence;
- crack–residual-stress driving-force amplification;
- dislocation–grain-boundary pile-up or absorption;
- vacancy–interstitial recombination or clustering;
- chemical-disorder–electronic-trap coupling;
- delamination–crack interfacial coupling.

The inferred interaction graph is not an atomistic or continuum simulation. Its outputs are reviewable candidates that identify where a physics-based model or experiment is needed.

The derived tensor reports:

- defect-kind distribution;
- mean and maximum criticality;
- mobile fraction;
- formation-energy coverage;
- density coverage;
- functional-label coverage;
- interaction density;
- heuristic cascade risk.

---

## 6. PhaseGraph-T

`PhaseGraph` stores phases and directed transitions with:

- activation barrier;
- driving force;
- characteristic time;
- reversibility;
- uncertainty;
- conditions;
- mechanism;
- epistemic status.

The graph can find a minimum cumulative barrier path, with optional nondimensionalization by `RT`. This is a path-search utility, not a complete phase-field or kinetic Monte Carlo solver.

A reversible transition is expanded into a reverse edge with a conservatively transformed barrier. Real systems may require a more detailed free-energy landscape and path-dependent kinetics.

---

## 7. Established engineering kernels

### Isotropic elasticity

`IsotropicElasticity` derives shear modulus, bulk modulus, Lamé parameter and a 6×6 Voigt stiffness matrix from Young's modulus and Poisson ratio. It validates the stable isotropic range `-1 < ν < 0.5`.

### Mixture bounds

`rule_of_mixtures` supports:

- Voigt isostrain estimate;
- Reuss isostress estimate;
- Hill average.

These are baseline estimates, not universal composite laws.

### Hall–Petch

`hall_petch_strength` implements the classical engineering form

```text
sigma_y = sigma_0 + k / sqrt(d)
```

It should not be extrapolated blindly to grain sizes where inverse Hall–Petch behavior or different mechanisms occur.

### Gibson–Ashby

`gibson_ashby_modulus` evaluates

```text
E* = C E_s (rho*/rho_s)^n
```

for a chosen coefficient and exponent. It is an explicit baseline for porous and architected materials, not a geometry-specific finite-element result.

### Fracture safety factor

`fracture_safety_factor` compares toughness with a mode-I stress-intensity estimate. Critical components require accepted standards, geometry-specific factors, inspection data and professional sign-off.

---

## 8. Energy functional

`EnergyFunctional` composes named energy terms and preserves which terms are established or exploratory.

Provided constructors include:

- small-strain scalar elastic energy;
- constant surface energy;
- sensible thermal energy;
- an information-complexity penalty.

The information penalty is labeled explicitly as an optimization term, not a thermodynamic energy. A user must not combine unlike units. The evaluator rejects a functional whose terms use incompatible units.

---

## 9. Calibration and uncertainty

The calibration module provides:

- ordinary linear calibration;
- residual standard deviation;
- coefficient of determination;
- instrument agreement metrics;
- bias, MAE, RMSE and normalized RMSE;
- optional coverage inside combined uncertainty.

The uncertainty module provides:

- intervals and intersections;
- deterministic quantiles;
- seeded Monte Carlo propagation;
- normal, uniform and triangular samplers;
- finite-difference sensitivity;
- combination of independent standard uncertainties.

A fixed seed is recorded in every Monte Carlo summary for reproducibility.

---

## 10. SolidCompiler-T

`SolidCompiler` ranks candidate genomes against explicit property objectives and constraints.

An objective includes:

- property name;
- target value and unit;
- tolerance;
- weight;
- target, maximize or minimize mode.

A constraint can be hard or soft. Hard violations force the total score to zero. Soft violations multiply a penalty. The final score blends objective fit with OAK quality so that a numerically attractive but poorly evidenced candidate does not dominate silently.

```python
from omega_solids_t.atlas import iter_archetypes
from omega_solids_t.inverse_design import (
    PropertyObjective,
    SolidCompiler,
    maximum_porosity,
)

compiler = SolidCompiler(
    [PropertyObjective("young_modulus", 100e9, "Pa", 50e9, mode="maximize")],
    [maximum_porosity(0.4)],
)

for candidate in compiler.rank(iter_archetypes())[:5]:
    print(candidate.genome.identifier, candidate.total_score)
```

A ranking does not prove synthesis, stability, safety, availability or cost. It is a transparent decision aid and a generator of discriminating next tests.

---

## 11. OAK-SolidGate

Eight gates are executable in R0.1.

### 11.1 Physical coherence

Checks property presence, units, porosity bounds, assumptions and epistemic labels.

### 11.2 Stability

Checks phase representation, defect-cascade warnings and the presence of a stability-oriented next experiment.

### 11.3 Reproducibility

Scores property metadata, named process steps and provenance.

### 11.4 Baselines

Searches for an explicit baseline, reference or comparison commitment in assumptions and next experiments.

### 11.5 Uncertainty

Measures how many encoded properties carry an uncertainty.

### 11.6 Fabricability

Checks process coverage, minimum-feature validity and whether a proposed design remains marked as needing coupons.

### 11.7 System function

Connects properties, applications and next experiments.

### 11.8 Hypergraph integrity

Builds the hypergraph, checks incidence consistency and requires one connected component.

The aggregate gate uses weighted scores but any failed gate blocks promotion. Passing OAK does not certify the material. It certifies only that the current research record met the encoded checks.

---

## 12. Adaptive unbounded frontier

The user requirement is explicit: no arbitrary permanent ceiling such as `max_ajout=1000`.

Ω-SOLID-T∞ implements this as a lazy source plus an adaptive controller:

```text
lazy candidate source
    -> disk-backed fingerprint ledger
    -> OAK quality filter
    -> streamed JSONL sink
    -> telemetry
    -> adaptive batch expansion/backpressure
    -> checkpoint
    -> M+ / M- ledgers
```

### What “unbounded” means here

- no fixed total-generation constant exists in the source;
- identifiers and variants can continue as long as the caller supplies resources;
- batches grow when latency, quality and acceptance permit;
- batches shrink under backpressure;
- saturation events are recorded in M⁻ with redesign candidates;
- successful capacity increases are recorded in M⁺;
- genomes stream to disk rather than accumulating in memory.

### What it does not mean

No real execution is physically infinite. Every run remains bounded by one of:

- an explicit finite `--work-items` experiment;
- an external stop predicate;
- storage and compute;
- provider/API limits;
- quality floor;
- safety, IP and legal controls;
- rollback and audit requirements.

Run ten thousand candidates:

```bash
omega-solids frontier \
  --work-items 10000 \
  --initial-batch 128 \
  --growth-factor 2 \
  --quality-floor 0.70 \
  --output-dir generated/omega_solids/frontier-10k
```

Run one hundred thousand by changing only the experimental budget:

```bash
omega-solids frontier --work-items 100000 --output-dir generated/omega_solids/frontier-100k
```

There is no code change and no permanent controller ceiling between these runs.

### Runtime outputs

- `accepted-genomes.jsonl`;
- `fingerprints.txt`;
- `frontier-events.jsonl`;
- `checkpoint.json`;
- `frontier-report.json`;
- `m_plus.jsonl` when capacity expands;
- `m_minus.jsonl` when quality or capacity saturates.

---

## 13. Materialized analysis bundle

`SolidPipeline.materialize` writes:

```text
solid-genome.json
solid-hypergraph.json
solid-hypergraph.graphml
cvcd-signature.json
oak-report.json
report.json
report.md
```

This is a DCT++-compatible research packet foundation: data, code path, testable claims, risks, status and next actions remain colocated.

---

## 14. JSON Schema

`schemas/solid_genome.schema.json` provides a Draft 2020-12 schema. Runtime dataclasses enforce cross-field constraints such as fraction sums that plain JSON Schema does not express cleanly without custom vocabularies.

The validation strategy is therefore layered:

1. JSON shape and enums through the schema;
2. cross-field invariants through `SolidGenome.from_dict`;
3. physics and evidence checks through OAK;
4. domain simulation and experiment outside the package.

---

## 15. Scientific boundaries

The package must not be used to claim that:

- a generated structure exists physically;
- a low energy guarantees synthesis;
- a simulation is a measurement;
- a CVCD similarity proves equal function;
- a defect heuristic is a mechanistic law;
- a hypergraph relation is causal evidence;
- a proposed lattice is manufacturable;
- a material is safe for critical, medical or pressure applications;
- an exploratory Cayley-Dickson representation is a new law of matter.

Promotion requires traceable data, calibrated instruments, baseline comparison, uncertainty, sensitivity analysis, independent reproduction when warranted, and human review.

---

## 16. Development roadmap

### R0.2 — Data adapters

- CIF and POSCAR import;
- PDB/mmCIF adapter for biological solids;
- generic tabular property import;
- explicit unit conversion layer;
- provenance identifiers and dataset licenses.

### R0.3 — Phase and microstructure solvers

- phase-field adapter;
- cellular automata grain growth;
- pore-network transport;
- discrete-element granular baseline;
- finite-element input generation.

### R0.4 — Characterization

- XRD peak and phase adapter;
- Raman/FTIR spectral family links;
- SEM/TEM/EBSD microstructure descriptors;
- tomography pore graph;
- FFWT-Solid multi-scale image kernel.

### R0.5 — Design and fabrication

- constraint-aware topology generation;
- Ω-3DP-T slicing/manufacturability bridge;
- coupon generator;
- uncertainty-aware optimization;
- active-learning experiment selection.

### R1.0 — Solid Operating System

- multi-source atlas;
- calibrated direct and inverse models;
- simulation adapters;
- experiment ledger;
- OAK promotion workflow;
- IPGate;
- reproducible material twin;
- adaptive campaign orchestration without arbitrary total-addition caps.

---

## 17. Quick start

```bash
python -m pytest -q tests/test_omega_solids_t.py
python -m omega_solids_t.cli list-archetypes
python -m omega_solids_t.cli analyze \
  --archetype architected_lattice \
  --output-dir generated/omega_solids/lattice
python examples/omega_solids_demo.py
```

---

## 18. Canonical statement

> Ω-SOLID-T∞ represents a solid as a dynamic multi-scale material hypergraph whose composition, bonding, order, geometry, defects, interfaces, process, history, fields and uncertainty jointly determine observable behavior. It compiles that representation into traceable genomes, CVCD signatures, hypergraphs, baseline models, candidate rankings, adaptive campaigns and OAK reports while preserving the boundary between established science, simulation, extrapolation, hypothesis, prototype and independent validation.
