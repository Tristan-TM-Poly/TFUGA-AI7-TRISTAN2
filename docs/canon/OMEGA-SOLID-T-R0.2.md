# Ω-SOLID-T∞ R0.2 — Solid Universe Compiler

**Status:** executable OAK-safe research infrastructure. Generated records are ontology cells, candidate specifications, evidence templates and mechanism mappings. They are not experimental discoveries, certified materials, safety approvals, fabrication guarantees, patentability conclusions or commercial performance claims.

## 1. Purpose

R0.2 expands Ω-SOLID-T∞ from twelve hand-authored archetypes into a deterministic, shardable and auditable universe of solid-material candidates. The architecture represents composition, order, topology, defects, processing, environment, mechanisms, provenance and uncertainty without assuming that enumeration creates truth.

The system separates five layers:

1. **Vocabulary:** 64 material worlds, 64 architectures, 16 defect profiles, 8 process profiles, 4 environments and 64 mechanism families.
2. **Logical campaign:** a mixed-radix search space with 524,288 base candidates and 2,097,152 contextual states.
3. **Hot atlas:** 8,192 selected candidate cells checked into Git for navigation and regression testing.
4. **Evidence layer:** 8,192 evidence templates that state what would be required to promote each candidate.
5. **Mechanism layer:** 4,096 world–mechanism mappings requiring domain review.

The checked-in materialization therefore contains 20,480 logical objects while the generator remains capable of traversing the complete finite campaign lazily.

## 2. No permanent total-candidate ceiling

The code contains no `MAX_CANDIDATES`, `MAX_ADDITIONS` or equivalent permanent ceiling. A concrete execution is always finite and must declare its range, partition size, resource budget, validation policy and rollback path.

```text
finite work request
→ mixed-radix range
→ lazy decoding
→ deterministic identifiers
→ OAK gates
→ atomic JSONL shards
→ hashes and manifests
→ checkpoint/resume integration
→ M⁺ or M⁻ result
```

A million logical candidates must not become a million GitHub files. The repository stores code, schemas, policies, manifests, hot projections and selected evidence records. Larger cold campaigns belong in compressed shards, object storage, Releases, Parquet, SQLite, DuckDB or graph stores with Git retaining hashes and provenance.

## 3. Campaign cardinality

The base campaign is:

```text
64 material worlds
× 64 architecture cells
× 16 defect profiles
× 8 process profiles
= 524,288 base candidates
```

Four environment profiles create:

```text
524,288 × 4 = 2,097,152 contextual candidate states
```

These values describe the default R0.2 experiment, not an architectural maximum. A future campaign may replace or extend any axis while preserving the same mixed-radix, partitioning and validation contracts.

## 4. The 64 worlds

The atlas covers metallic, ceramic, glass, molecular, polymeric, composite, porous, granular, soft, biological, low-dimensional, electronic, electrochemical, magnetic, quantum, photonic, phononic, metamaterial, functional, nonequilibrium, porous-crystal, geological, extreme and Tristan-exploratory domains.

The sixty-fourth world is `unknown-solid`. Its purpose is quarantine: it stores non-synthesized structures, unexplained anomalies, speculative mechanisms and unknown-unknown candidates. Objects in this world automatically fail the safety gate and cannot be promoted without external evidence.

## 5. Architecture grammar

Sixty-four architectures are generated from eight topology families and eight order classes.

Topologies:

- dense bulk;
- layered;
- fibre network;
- particle network;
- open cell;
- closed cell;
- hierarchical lattice;
- interpenetrating network.

Order classes:

- periodic;
- quasiperiodic;
- polycrystalline;
- nanocrystalline;
- amorphous;
- semicrystalline;
- jammed;
- programmed nonequilibrium.

The Cartesian construction is an ontology stress test, not a claim that every pair is physically realizable. OAK gates and later scientific models decide which combinations remain coherent.

## 6. Defect profiles

Sixteen profiles range from an idealized pristine reference to a coupled multiscale critical state. Each profile records defect kinds, heuristic criticality and mobility class. Criticality is a triage descriptor, not a fracture probability.

Profiles include vacancies, interstitials, substitutional disorder, dislocation networks, grain boundaries, stacking faults, dilute and connected porosity, inclusions, microcracks, residual stresses, electronic traps, interfacial debonding and irradiation cascades.

## 7. Process profiles

Eight process genomes represent equilibrium growth, rapid solidification, powder consolidation, additive layerwise processing, solution deposition, polymerization/cure, thermomechanical treatment and biogenic assembly.

A process profile identifies a family of steps. It does not specify sufficient parameters for manufacturing. Temperature trajectories, atmospheres, rates, equipment, feedstock purity, calibration, yield and quality control remain required before fabrication claims.

## 8. Environment profiles

R0.2 uses ambient dry, humid reactive, thermal extreme and field-loaded contexts. Every environment includes explicit temperature and pressure units. The medium remains qualitative where a composition has not been supplied.

## 9. Mechanism atlas

Sixty-four mechanism labels arise from eight physical categories and eight variants. Categories are elastic, plastic, fracture, thermal, electronic, ionic, magnetic and optical. Variants are local, collective, interface-controlled, defect-controlled, transport-limited, kinetic, multiscale and nonequilibrium.

A candidate receives four deterministic mechanism labels. These labels identify hypotheses to test. They do not assert that the mechanisms are active or dominant.

## 10. Candidate identity

Every candidate contains:

- campaign identifier and logical index;
- material world;
- architecture;
- defect profile;
- process profile;
- environment profile;
- candidate mechanisms;
- numerical and categorical descriptors;
- required OAK checks;
- epistemic status;
- provenance identifiers;
- deterministic SHA-256 fingerprint.

The fingerprint changes when any scientific identity field changes. Numeric canonicalization prevents false differences between values such as `1` and `1.0`.

## 11. Twelve OAK gates

R0.2 executes twelve gates:

1. structural schema;
2. vocabulary resolution;
3. explicit units;
4. domain of validity;
5. stability and defect criticality;
6. mechanism identifiability;
7. baseline commitment;
8. uncertainty commitment;
9. counter-model or negative control;
10. process/fabricability coverage;
11. safety classification;
12. provenance coverage.

The gates are deliberately conservative. Generated candidates normally remain exploratory because they lack experimental evidence and counter-model testing. Unknown, nuclear, irradiation and high-pressure classes require specialist safety review.

## 12. Hypergraph representation

`SolidHypergraph` keeps candidate context as a true multi-member relation rather than flattening it into unrelated pairwise edges. Nodes include candidates, worlds, architectures, defects, processes, environments and mechanisms. Hyperedges encode context and hypothesized mechanisms.

GraphML lacks general hyperedges, so the exporter represents each hyperedge as an explicit node joined to its members. This is a projection for graph tooling, not a claim that a hyperedge is a physical particle.

## 13. SolidGenome R2

The package retains a richer `SolidGenomeR2` object for measured, simulated or proposed materials. It separates composition, bond vector, structure, defects, interfaces, process history, properties, environment, assumptions, risks, next experiments, evidence and a U² uncertainty tensor.

Composition and bond vectors must each sum to one. Properties retain value, unit, uncertainty, epistemic status and source identifier.

## 14. U² uncertainty

`U2Tensor` separates aleatoric, epistemic, model-form, measurement, provenance and unknown-unknown components. Its aggregate is a triage norm, not a calibrated probability of error.

The uncertainty module also provides intervals, independent uncertainty combination and seeded Monte Carlo propagation. Seed recording makes stochastic summaries reproducible.

## 15. Engineering baselines

The package includes deliberately simple, transparent baselines:

- isotropic elastic conversion;
- Voigt, Reuss and Hill mixture estimates;
- Hall–Petch relation;
- Gibson–Ashby modulus scaling;
- mode-I fracture safety factor;
- Arrhenius diffusivity;
- constrained thermal stress.

Each formula has a limited domain. None should be extrapolated blindly to nanoscale, phase-changing, anisotropic, nonlinear or safety-critical regimes.

## 16. Inverse-design compiler

`SolidCompiler` ranks candidates against explicit objectives and hard constraints. The score multiplies objective fit by OAK quality so that a numerically attractive but poorly supported candidate cannot silently dominate.

The current descriptors are ontology-level heuristics. Real design campaigns must replace them with calibrated models, measured properties and uncertainty-aware constraints.

## 17. Materialized hot atlas

The hot atlas selects:

```text
64 worlds × 16 architectures × 8 process profiles = 8,192 candidates
```

A deterministic defect profile and one of four environments are assigned to each cell. This projection gives broad coverage while keeping repository size reviewable.

For each hot candidate, an evidence template specifies required claim types, methods, OAK status, score and blockers. Evidence templates are requirements, not evidence.

The world–mechanism matrix contains:

```text
64 worlds × 64 mechanisms = 4,096 mappings
```

Each mapping is marked `candidate_mapping_requires_domain_review`.

## 18. Integrity and reproducibility

Materialization uses atomic temporary files followed by replacement. Every shard records SHA-256, byte count and record count. Manifests allow independent integrity checks.

Tests verify:

- vocabulary cardinality and uniqueness;
- mixed-radix round trips;
- exact campaign cardinalities;
- deterministic candidate fingerprints;
- twelve OAK gates;
- automatic quarantine of critical classes;
- hypergraph integrity;
- engineering baseline limits;
- uncertainty reproducibility;
- JSONL sharding and digest verification;
- exact hot-atlas, evidence and mapping counts;
- unique candidate identifiers and fingerprints;
- a 100,000-candidate lazy stream under a memory ceiling;
- partition coverage without gaps or overlaps.

## 19. CLI

```bash
omega-solids vocab
omega-solids manifest
omega-solids decode 424242 --environment 2
omega-solids oak 424242 --environment 2
omega-solids plan --target-records-per-partition 8192 --output plan.json
omega-solids emit --start 0 --stop 100000 --records-per-shard 4096 --output-dir generated/run
omega-solids graph 424242 --output-dir generated/graph
omega-solids materialized-stats
omega-solids search "microcrack"
```

## 20. Scientific boundaries

R0.2 must never claim that:

- enumeration equals discovery;
- a valid schema implies physical stability;
- an OAK score is a probability of truth;
- a mechanism label proves causality;
- a process family guarantees manufacturability;
- a generated candidate is patentable;
- a hot-atlas record is measured data;
- a numerical fingerprint is scientific validation;
- a low defect-criticality score certifies safety;
- a model without independent evidence is ready for engineering release.

## 21. Next R0.3 fronts

The next scientifically valuable fronts are:

1. unit-aware process trajectories;
2. phase and interface graphs;
3. material-property evidence ingestion;
4. calibrated defect interactions;
5. process–structure–property causal models;
6. FFWT microstructure baselines;
7. external data provenance;
8. checkpointed million-candidate emission;
9. Parquet and DuckDB cold-atlas adapters;
10. inverse-design tasks with real reference datasets.

## 22. Canonical statement

> Ω-SOLID-T∞ R0.2 is a deterministic, shardable and OAK-safe compiler of solid-material candidate spaces. It represents material worlds, architectures, defects, processes, environments and mechanisms as auditable objects; generates 524,288 base candidates and 2,097,152 contextual states without a permanent total-candidate ceiling; materializes a 20,480-object hot evidence atlas; and prevents automatic promotion from enumeration to discovery, fabrication or safety claims.
