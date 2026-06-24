# Ω-ST v2 / Ω-ST+++ — Sciences de Tristan extrêmes

**Status:** v2/+ ultra canon seed.  
**Purpose:** extend the current `ScienceCard + Bayes-Tristan + AIT-OAK + CLI + tests` layer into a full personal Science OS: generative, verifiable, self-prioritizing, multi-agent, prototypable and publication-aware.

> Les Sciences de Tristan sont une machine à transformer l'imagination en trajectoires vérifiables.

## 0. Current layer versus v2

Current GitHub layer:

```text
idea -> ScienceCard -> Bayes-Tristan -> AIT-OAK -> next action
```

v2 layer:

```text
idea -> HGFM -> LOG -> CVCD -> EXP -> Bayes-Tristan -> AIT-OAK
     -> Prototype -> Benchmark -> Residue -> M+/M- -> Canon -> Paper/Product
```

Ω-ST+++ layer:

```text
Idea -> Living card -> HGFM -> LOG -> CVCD -> EXP -> Bayes-Tristan tensor
     -> OAKCourt -> Prototype -> Benchmark -> Residue -> M-/M+
     -> Canon -> Paper/Tool
```

Canonical equation:

```text
S_{t+1} = Canon(Memory(OAK(Bench(Proto(BayesT(EXP(CVCD(LOG(HGFM(S_t,D_t,E_t,R_t))))))))))
```

Ω-ST+++ equation:

```text
S_{t+1} = Canon(Memory(OAKCourt(Bench(Proto(BayesT^⊗(EXP(CVCD(LOG(HGFM(S_t,D_t,P_t,R_t))))))))))
```

Core law:

```text
Une idée ne devient pas vraie parce qu'elle est belle.
Elle devient scientifique quand elle produit une trajectoire vérifiable.
```

## 1. From ScienceCard to ScienceOrganism

A `ScienceCard` is a useful fiche. A `ScienceOrganism` is a minimal living scientific organism.

```yaml
science_organism:
  id: ST-O-0001
  name: FFWT-HAC-CVCD
  type: hypothesis

  genome:
    statement: "clear, testable, falsifiable hypothesis"
    definitions: []
    equations: []
    assumptions: []
    predictions: []
    falsifiers: []

  phenotype:
    branch: ffwt_hac_cvcd
    visible_claim: null
    safe_claim: null
    prototype_signature: null
    publication_signature: null

  metabolism:
    inputs:
      - data
      - corpus
      - equations
      - signals
    transformations:
      - HGFM
      - LOG
      - CVCD
      - EXP
      - BayesT
      - OAK
    outputs:
      - tests
      - prototypes
      - reports
      - residues
      - papers

  cognition:
    bayes_tristan_tensor:
      truth: null
      utility: null
      fertility: null
      testability: null
      safety: null
      compressibility: null
      novelty: null
      value: null
    oak_status: Omega_2
    canon_score: null
    priority_score: null
    risk_score: null

  immune_system:
    memory_negative:
      - anti_rules
      - failed_claims
      - known_risks
    claim_transmutations:
      - raw_claim
      - safe_claim
      - testable_claim

  embodiment:
    prototype: null
    benchmark: null
    datasets: []
    metrics: []
    baselines: []
    code_path: null

  reproduction:
    child_hypotheses: []
    paper_seed: null
    github_issue: null
    next_pr: null
    future_experiments: []
```

A theory has:

```text
genome + phenotype + metabolism + cognition + immune system + body + descendants
```

The corpus becomes a biosphere of living knowledge, not only a file collection.

## 2. Tristan Discovery Loop

Add a conceptual and executable loop:

```python
def tristan_discovery_loop(science_card, data=None):
    graph_node = hgfm_insert(science_card)
    compressed = log_compress(graph_node)
    invariants = cvcd_extract(compressed)
    variants = exp_generate(invariants)

    scored = bayes_tristan_score(variants)
    reviewed = ait_oak_review(scored)

    prototype = build_minimal_prototype(reviewed)
    benchmark = run_baselines(prototype, data)

    residue = compute_residue(benchmark)
    memory_update = update_memory(residue, benchmark)

    return canonize(
        card=science_card,
        score=scored,
        review=reviewed,
        prototype=prototype,
        benchmark=benchmark,
        residue=residue,
        memory=memory_update,
    )
```

Law:

```text
pas de canonisation sans boucle complète
```

If a stage is missing, it must be explicit:

```yaml
prototype: null
reason: "not implemented yet"
oak_blocker: "no benchmark"
```

## 3. Bayes-Tristan tensor

The current vector is:

```text
p = (true, useful, fertile, testable, safe, compressible, novel, valuable)
```

v2 tensor:

```text
P_T(H) ∈ [0,1]^(axes × layers × time)
```

Layers include: mathematical, computational, physical, empirical, engineering, publication, product.

```yaml
bayes_tristan_tensor:
  axes:
    true: 0.55
    useful: 0.90
    fertile: 0.95
    testable: 0.90
    safe: 0.95
    compressible: 0.80
    novel: 0.80
    valuable: 0.85

  layers:
    mathematical:
      true: 0.60
      testable: 0.70
    computational:
      true: 0.75
      testable: 0.95
    physical:
      true: 0.35
      testable: 0.65
    publication:
      useful: 0.80
      valuable: 0.70

  version_history:
    v0:
      true: 0.40
      note: "intuition"
    v1:
      true: 0.55
      note: "after formulation"
```

Key hygiene rule:

```text
true in simulation != true physically
```

Bayes-Tristan v2 must distinguish:

```text
p_math, p_simulation, p_empirical, p_engineering, p_publication, p_product
```

## 4. OAKCourt: scientific tribunal

AIT-OAK gives tests, baselines and falsifiers. OAKCourt becomes a multi-role tribunal:

```text
AIT-Prosecutor       attacks the theory
AIT-Defender         formulates the strongest version
AIT-Experimentalist  proposes tests
AIT-Mathematician    seeks definitions/proofs/counterexamples
AIT-Engineer         proposes minimal prototype
AIT-Reviewer         prepares publication critique
AIT-MemoryMinus      applies anti-rules
AIT-Canonizer        decides status
```

Canonical output:

```yaml
oak_court_review:
  claim_id:
  claim:
  strongest_version:
  weakest_version:
  safe_version:

  prosecutor:
    objections:
      - missing definitions
      - no baseline
      - no falsifier
      - risk of overclaim
    fatal_risks: []

  defender:
    strongest_arguments: []
    reformulation: []
    protected_core: []

  experimentalist:
    minimal_test:
    ideal_test:
    measurable_predictions: []
    required_data: []
    metrics: []

  mathematician:
    definitions_needed: []
    theorem_candidates: []
    counterexample_search: []
    edge_cases: []

  engineer:
    minimal_prototype:
    files_to_create: []
    expected_runtime:
    dependencies: []
    baseline_implementation:

  reviewer:
    paper_strengths: []
    paper_weaknesses: []
    likely_peer_review_objections: []
    required_figures: []

  memory_minus:
    triggered_anti_rules: []
    previous_failures: []
    forbidden_promotions: []

  verdict:
    current_status:
    recommended_status:
    decision: promote | hold | split | transmute | reject
    promotion_blockers: []
    next_action:
```

## 5. CVCD: fertile invariants

Formalization:

```text
CVCD(X) = (I, F, R, G)
```

where:

- `I`: invariants;
- `F`: useful features;
- `R`: structured residues;
- `G`: hypothesis generators.

An invariant is a quantity stable under a transformation family.

```text
I_i(X) = quantity stable under transformations T
```

Fertility:

```text
Fertility(I_i) = α N_hypotheses + β N_tests + γ N_prototypes + δ Compression - λ Ambiguity
```

Canonical invariant card:

```yaml
cvcd_invariant:
  name:
  stability_under:
  extracted_from:
  compression_gain:
  generated_hypotheses:
  generated_tests:
  generated_prototypes:
  ambiguity:
  oak_status:
```

## 6. LOG/EXP: controlled fertile compression

Operators:

```text
LOG: X -> z
EXP: z -> {X_1, ..., X_n}
X = EXP(LOG(X)) + R
```

Quality:

```text
Q_LOG/EXP = αC + βG + γT - δR - εN
```

where `C` is compression, `G` generativity, `T` testability, `R` residue, `N` unfiltered noise/speculation.

Rule:

```text
EXP sans OAK est interdit comme canon ; autorisé seulement comme graine.
```

## 7. HGFM edge typing

Every scientific relation must be typed.

```yaml
edge_types:
  inspires:
    strength: weak
    promotes_oak: false
  analogizes:
    strength: weak
    promotes_oak: false
  formalizes:
    strength: medium
    promotes_oak: true
  predicts:
    strength: medium
    promotes_oak: true
  tests:
    strength: strong
    promotes_oak: true
  refutes:
    strength: very_strong
    promotes_oak: true
  prototypes:
    strength: strong
    promotes_oak: true
  reproduces:
    strength: very_strong
    promotes_oak: true
  canonizes:
    strength: final_gate
    promotes_oak: true
```

Example:

```yaml
edge:
  id: E-0001
  source: ST-H-0002
  target: ST-P-0004
  type: prototypes
  confidence: 0.82
  oak_status: Omega_3
  evidence:
    - "fractal_rlc_lab implements graph spectral response"
  residue:
    - "physical material interpretation still untested"
```

Law:

```text
Une analogie peut inspirer ; seul un test peut promouvoir.
```

## 8. MemoryMinusEngine: epistemic immune system

```text
M- = anti-dataset de lucidité
```

Each error becomes a defense rule.

```yaml
memory_minus_rules:
  - id: M-_PHYS_001
    name: no_material_claim_without_measurement
    trigger:
      branch: physics | materials
      keywords:
        - superconductivity
        - infinite
        - topological phase
        - zero resistance
    required_checks:
      - units
      - dimensional_analysis
      - physical_mechanism
      - measurable_prediction
      - baseline
      - falsifier
      - experimental_criterion
    action:
      - transmute_claim
      - lower_oak_status
      - require_test

  - id: M-_MATH_001
    name: no_theorem_without_definitions
    trigger:
      keywords:
        - theorem
        - proof
        - solves
        - demonstrates
    required_checks:
      - definitions
      - assumptions
      - domain
      - proof_steps
      - counterexample_search
    action:
      - block_promotion_to_Omega_6

  - id: M-_ALG_001
    name: no_exotic_algebra_without_invariant
    trigger:
      keywords:
        - quaternion
        - octonion
        - sedenion
        - hypernumber
    required_checks:
      - real_projection
      - invariant_measured
      - baseline_comparison
      - numerical_stability
      - interpretability
    action:
      - require_ablation

  - id: M-_AI_001
    name: no_agent_without_benchmark
    trigger:
      keywords:
        - AIT
        - agent
        - autonomous
        - improves
    required_checks:
      - task
      - metric
      - baseline
      - failure_modes
      - evaluation_set
    action:
      - require_benchmark
```

Law:

```text
Erreur -> anti-règle -> protection future
```

## 9. ClaimTransmuter

The ClaimTransmuter converts strong raw claims into safe, testable, falsifiable claims.

```text
ClaimTransmuter(C) = (C_raw, C_safe, C_testable, C_falsifiable, C_promotable)
```

Example:

```yaml
raw_claim: >
  Les fractales conductrices peuvent devenir des supraconducteurs topologiques.

safe_claim: >
  Les géométries conductrices fractales peuvent être explorées comme candidates
  pour produire des modes résonants, localisés ou topologiques dans des réseaux
  simulés. Une revendication de supraconductivité exige des critères physiques
  supplémentaires : résistance nulle, effet Meissner, gap, cohérence de phase
  et reproductibilité expérimentale.

testable_claim: >
  Un réseau LC/RLC fractal conducteur devrait produire une signature spectrale
  multi-échelle distinguable de réseaux réguliers ou aléatoires.

falsifiers:
  - aucune différence robuste avec les baselines
  - modes non stables sous perturbation
  - signature due uniquement à un artefact numérique
  - absence de mécanisme physique plausible pour une propriété matérielle forte

promotion_path:
  Omega_1: définir le graphe fractal et ses composants
  Omega_2: formuler les matrices RLC et prédictions spectrales
  Omega_3: simuler les modes propres
  Omega_4: comparer à baselines
  Omega_5: tester robustesse
  Omega_6: preuve ou validation expérimentale forte
```

Law:

```text
Le ClaimTransmuter ne réduit pas la puissance d'une idée ; il lui donne une trajectoire de survie scientifique.
```

## 10. Eight root prototypes

1. `bayes_tristan_engine`: add ranking profiles for exploration, publication, prototype.
2. `ait_oak_court`: multi-agent review.
3. `claim_transmuter`: raw vision -> testable hypothesis.
4. `memory_minus_engine`: detect anti-rules.
5. `cvcd_invariant_extractor`: symbolic first, numerical later.
6. `ffwt_hac_cvcd_benchmark`: first real scientific benchmark.
7. `fractal_rlc_lab`: graph -> RLC matrices -> modes -> response -> report.
8. `theory_to_paper`: mature card + results + limitations -> manuscript scaffold.

## 11. Target architecture

```text
sage_tristan/sciences_tristan/
  __init__.py
  __main__.py

  core/
    science_card.py
    science_organism.py
    oak_status.py
    bayes_vector.py
    bayes_tensor.py
    canon_score.py
    promotion_gate.py
    residue.py
    memory.py

  engines/
    bayes_tristan_engine.py
    ait_oak.py
    oak_court.py
    claim_transmuter.py
    memory_minus_engine.py
    residue_miner.py
    hgfm_mapper.py
    cvcd_engine.py
    log_exp_engine.py
    ablation_engine.py
    paper_forge.py

  branch_dna/
    math.py
    physics.py
    signals.py
    materials.py
    ait.py

  prototypes/
    ffwt_hac_cvcd/
      features.py
      benchmark.py
      report.py
    fractal_rlc_lab/
      graphs.py
      rlc_matrix.py
      spectrum.py
      report.py
    materials_cvcd_scanner/
      spectra.py
      features.py
      report.py

  cli/
    intake.py
    rank.py
    review.py
    transmute.py
    audit.py
    gates.py
    dashboard.py

  reports/
    oak_report.py
    portfolio_report.py
    paper_seed.py
    dashboard.py
```

## 12. Test expansion

Critical tests:

```text
test_science_card.py
test_science_organism.py
test_bayes_vector.py
test_bayes_tensor.py
test_priority_vs_canon_score.py
test_promotion_gates.py
test_claim_transmuter.py
test_memory_minus_engine.py
test_oak_court.py
test_residue_miner.py
test_hgfm_edge_types.py
test_branch_dna_physics.py
test_branch_dna_math.py
test_branch_dna_signals.py
test_ffwt_feature_ablation.py
test_fractal_rlc_dimension_check.py
test_cli_rank.py
test_cli_review.py
test_cli_transmute.py
test_cli_audit.py
test_examples_validate_json.py
test_examples_validate_yaml.py
test_no_high_fertility_equals_truth.py
test_no_physics_claim_without_measurement.py
test_no_theorem_without_definition.py
test_no_exotic_algebra_without_projection.py
test_no_agent_without_benchmark.py
test_oak_gap_detection.py
test_residue_generates_child_hypothesis.py
test_paper_seed_generation.py
test_dashboard_report.py
test_zero_touch_pipeline_stub.py
```

Essential test laws:

```python
def test_high_fertility_is_not_high_truth():
    card = make_card(true=0.2, fertile=0.95)
    assert card.bayes.true < card.bayes.fertile
    assert card.canon_score < card.priority_score


def test_physics_claim_requires_measurement():
    card = make_card(branch="physics", statement="fractal conductor implies superconductivity")
    review = OAKCourt().review(card)
    assert "measurement" in review.required_checks
    assert review.verdict != "promote_to_canon"


def test_residue_becomes_child_hypothesis():
    residue = Residue(source="benchmark", gap="fails on chirp signals")
    children = ResidueMiner().mine(residue)
    assert len(children) >= 1
```

## 13. CanonScore versus PriorityScore

Priority is not canonization.

```text
PriorityScore high != CanonScore high
```

PriorityScore:

```text
PriorityScore = 0.20U + 0.20F + 0.20T + 0.15S + 0.15V + 0.10N
```

CanonScore:

```text
CanonScore = 0.25E + 0.20R + 0.20P + 0.15T + 0.10L + 0.10S
```

where evidence, reproducibility, validated prototype/proof, truth estimate, known limits and stability matter more than raw novelty.

## 14. Promotion gates

Each OAK transition must pass a gate.

```yaml
promotion_gates:
  Omega_0_to_1:
    requires:
      - name
      - branch
      - one_sentence_statement
    blocks_if:
      - no clear object

  Omega_1_to_2:
    requires:
      - assumptions
      - predictions
      - falsifiers
      - mathematical_or_operational_form
    blocks_if:
      - poetic only
      - no testable meaning

  Omega_2_to_3:
    requires:
      - prototype_plan
      - baseline
      - metric
      - minimal_data_or_simulation
    blocks_if:
      - no measurable output

  Omega_3_to_4:
    requires:
      - executed_test
      - benchmark_result
      - recorded_residue
    blocks_if:
      - prototype not run
      - no comparison

  Omega_4_to_5:
    requires:
      - repeated_runs
      - ablation
      - robustness_check
    blocks_if:
      - single lucky result

  Omega_5_to_6:
    requires:
      - proof_or_strong_validation
      - limitations
      - external_comparison
    blocks_if:
      - no independent support

  Omega_6_to_7:
    requires:
      - usable_tool
      - documentation
      - reproducible_example
    blocks_if:
      - not usable by another person

  Omega_7_to_8:
    requires:
      - stable integration
      - canonical_documentation
      - long_term_maintenance
    blocks_if:
      - abandoned_or_unstable
```

Law:

```text
OAK ne tue pas les idées ; OAK empêche les faux couronnements.
```

## 15. Physics branch hygiene

```yaml
physical_claim_checklist:
  required:
    - units
    - dimensional_analysis
    - conservation_laws
    - mechanism
    - measurable_prediction
    - baseline
    - falsifier
    - known_literature_slot
    - simulation_or_experiment

  forbidden_without_evidence:
    - "proves superconductivity"
    - "violates thermodynamics"
    - "infinite energy"
    - "guaranteed topological phase"
```

Prudent fractal formulation:

```text
conductive fractals -> multi-scale resonances -> candidate localized/topological modes -> transport tests -> prudent material hypothesis
```

Not:

```text
fractal => superconductor
```

But:

```text
fractal => fertile geometry for non-trivial physical signatures
```

## 16. FFWT-HAC-CVCD formalization

Signal:

```text
X ∈ R^(N×d)
C_{j,k}^{(A)} = FFWT_A(X)_{j,k}
Cov_R(X,Y) = E[(X-μ_X)(Y-μ_Y)]
Cov_A(X,Y) = E[(X-μ_X) conjugate(Y-μ_Y)]
Delta_comm(a,b)=ab-ba
Delta_assoc(a,b,c)=(ab)c-a(bc)
```

Hypercoherence:

```text
K_T(X,Y) = (rho_R, rho_C, rho_H, Delta_comm, Delta_assoc, K_scale, K_fractal, R_residue)
```

Benchmark output:

```yaml
ffwt_hac_cvcd_report:
  dataset:
  task:
  baselines:
  metrics:
  real_projection_result:
  complex_phase_gain:
  quaternionic_orientation_gain:
  octonionic_assoc_signal:
  ablation:
  best_feature_set:
  failure_modes:
  oak_status:
```

## 17. Fractal RLC Lab formalization

Graph:

```text
G=(V,E)
e_ij -> (R_ij, L_ij, C_ij)
L_G q¨ + R_G q˙ + C_G^{-1} q = f(t)
```

Frequency-domain edge admittance:

```text
Y_e(ω) = 1 / (R_e + iωL_e + 1/(iωC_e))
Y_G(ω) = B diag(Y_e(ω)) B^T
Y_G(ω)V(ω)=I(ω)
```

Spectral signature:

```text
Σ_G = {ω: det(Y_G(ω))≈0 or response maximal}
```

Invariants:

```text
I_G = (β_1(G), dim_F(G), λ_k(L_G), IPR(ψ_k), Q_k, H_spectral)
```

Prudent claim:

```text
Les graphes fractals RLC peuvent être étudiés par signatures de réponse fréquentielle.
```

## 18. Theory-to-Paper / PaperForge

Each mature card can become a paper seed.

```yaml
paper_seed:
  title:
  subtitle:
  abstract:
  problem:
  contribution:
  related_work_slots:
    - classical baseline
    - closest method
    - known limitation
  method:
  theorem_or_algorithm:
  experiments:
  results:
  limitations:
  reproducibility:
  conclusion:
  future_work:
```

FFWT-HAC-CVCD example:

```yaml
paper_seed:
  title: "Multi-Scale Hyperalgebraic Coherence Features for Structured Signal Analysis"
  contribution:
    - "introduce a modular feature pipeline combining fractal wavelet decomposition with algebra-aware coherence"
    - "separate real, complex, quaternionic and higher-algebra projections"
    - "evaluate all extensions with ablation against classical baselines"
  limitations:
    - "higher algebras are exploratory until they produce metric gains or interpretable invariants"
    - "real-valued projections remain the robust comparison layer"
```

## 19. Zero-touch Science OS

Future commands:

```bash
python -m sage_tristan.sciences_tristan intake idea.md --branch physics
python -m sage_tristan.sciences_tristan transmute card.json
python -m sage_tristan.sciences_tristan rank portfolio.json --profile prototype
python -m sage_tristan.sciences_tristan review portfolio.json --oak-court
python -m sage_tristan.sciences_tristan audit portfolio.json
python -m sage_tristan.sciences_tristan gates card.json
python -m sage_tristan.sciences_tristan scaffold-prototype card.json
python -m sage_tristan.sciences_tristan residue result.json
python -m sage_tristan.sciences_tristan paper card.json
python -m sage_tristan.sciences_tristan dashboard portfolio.json
```

Pipeline:

```text
idea.md -> science_card.json -> transmuted_card.json -> oak_court_review.json
        -> prototype_plan.md -> test_contract.yaml -> benchmark_report.json
        -> residue_cards.json -> canon_update.md -> paper_seed.md
```

## 20. Philosophy v2

```text
Toute intuition est une graine.
Toute erreur est un anticorps.
Tout résidu est une mine.
Tout prototype est un pont.
Toute validation est une promotion.
Tout canon reste vivant.
```

Manifesto:

```text
Les Sciences de Tristan ne cherchent pas à avoir raison immédiatement.
Elles cherchent à transformer chaque idée en une trajectoire vérifiable.

Une idée peut être brillante sans être vraie.
Une idée peut être fausse mais fertile.
Une erreur peut devenir une règle.
Un résidu peut devenir une découverte.
Un prototype peut devenir une preuve opérationnelle.
Une théorie peut devenir un outil.
Un outil peut devenir une science.
Une science peut devenir un moteur de sciences.

Vision maximale.
Validation maximale.
Mémoire maximale.
Prototype minimal.
Canon vivant.
```

## 21. Module hierarchy

```text
Ω-ST_v2 = Ω_Vision + Ω_Forme + Ω_Test + Ω_Mémoire + Ω_Prototype + Ω_Canon
```

- `Ω_Vision`: capture, EXP, hypothesis generation, analogies, controlled imagination.
- `Ω_Forme`: ScienceCard, definitions, equations, invariants, formalization.
- `Ω_Test`: OAK, baselines, metrics, falsifiers, benchmarks.
- `Ω_Mémoire`: M+, M-, residues, anti-rules, status history.
- `Ω_Prototype`: code, simulations, notebooks, agents, CLI, reports.
- `Ω_Canon`: docs, proofs, publications, README, books, articles, stable versions.

## 22. Sixteen ideal next PRs

1. Add ClaimTransmuter for safe scientific reformulation.
2. Add OAKCourt multi-role review engine.
3. Add MemoryMinus anti-rule engine.
4. Add CanonScore and PromotionGate models.
5. Add ScienceCard JSON validation tests.
6. Add CLI rank/review/transmute/audit.
7. Add FFWT-HAC-CVCD benchmark scaffold.
8. Add Fractal RLC Lab graph simulator scaffold.
9. Add Materials CVCD Scanner scaffold.
10. Add Theory-to-Paper generator.
11. Add HGFM Corpus Mapper.
12. Add GitHub Actions CI.
13. Add portfolio dashboard report.
14. Add examples for physics/materials/math/AIT.
15. Add OAK negative-memory audit.
16. Add publication roadmap Volume I.

## 23. README short insert

```markdown
## Ω-ST v2 Direction

The next evolution of Sciences de Tristan turns the canon into a full discovery loop:

```text
idea -> ScienceCard -> HGFM -> LOG/CVCD/EXP -> Bayes-Tristan -> AIT-OAK
     -> prototype -> benchmark -> residue -> M+/M- -> canon -> paper/product
```

Key principles:

- high fertility is not high truth;
- every strong claim needs a falsifier;
- every prototype needs a baseline;
- every failure becomes memory-negative;
- every residue is a candidate discovery;
- every canon item remains revisable under stronger evidence.
```

## 24. First eight coding priorities

1. `ClaimTransmuter`
2. `PromotionGate`
3. `CanonScore`
4. `MemoryMinusEngine`
5. `OAKCourt`
6. `CLI audit`
7. `examples/sciences_tristan_physics.json`
8. `tests/test_claim_hygiene.py`

## 25. ResidueMiner

Residue:

```text
R = X - X_hat
```

Residue card:

```yaml
residue:
  id: ST-R-0007
  source_model: FFWT-HAC-CVCD-v0
  observed_gap: "model fails on high-noise chirp signals"
  possible_causes:
    - missing phase feature
    - wrong scale window
    - baseline stronger than expected
    - dataset artifact
  fertility_score: 0.82
  next_tests:
    - add chirp-specific synthetic dataset
    - compare complex vs real wavelet features
    - test robustness under variable SNR
  possible_child_hypotheses:
    - "phase instability is a useful anomaly feature"
    - "scale-window adaptation improves robustness"
```

Law:

```text
Un résidu structuré est une hypothèse embryonnaire.
```

## 26. TheoryGenome

```yaml
theory_genome:
  primitive_objects:
    - nodes
    - hyperedges
    - signals
    - residues
  operations:
    - compose
    - compress
    - expand
    - test
    - canonize
  invariants:
    - stability_under_transform
    - compression_gain
    - predictive_gain
    - residue_structure
  laws:
    - every_claim_has_status
    - every_model_has_residue
    - every_promotion_has_gate
  forbidden_mutations:
    - promote_without_test
    - confuse_fertility_with_truth
    - ignore_negative_memory
  reproduction_rules:
    - generate_child_hypothesis
    - generate_prototype_stub
    - generate_oak_test
    - generate_paper_seed
```

## 27. ExperimentContract

```yaml
experiment_contract:
  id: EXP-FFWT-0001
  hypothesis: ST-H-0001
  input_data:
    type: synthetic_multiscale_signals
    size:
    generation_seed:
  baselines:
    - FFT
    - wavelet
    - PCA
  method:
    - FFWT
    - HAC
    - CVCD features
  metrics:
    - accuracy
    - F1
    - AUROC
    - robustness_noise
    - runtime
  success_condition:
    - "improves at least one metric without unacceptable cost"
  falsification_condition:
    - "no improvement after fair ablation and baseline comparison"
  residue_policy:
    - "store all failures as residue cards"
  promotion_policy:
    if_success: Omega_4
    if_failure: Omega_2_with_memory_minus
```

Law:

```text
Pas d'expérience sans contrat ; pas de résultat sans résidu.
```

## 28. PrototypeContract

```yaml
prototype_contract:
  id: PROTO-RLC-0001
  name: fractal_rlc_lab
  proves:
    - "we can simulate spectral response of a fractal RLC graph"
  does_not_prove:
    - "real material superconductivity"
    - "experimental topological phase"
    - "device feasibility"
  required_for_promotion:
    - graph generator
    - matrix builder
    - eigenmode computation
    - baseline comparison
    - perturbation robustness
  outputs:
    - spectral_report.json
    - plots
    - residue_cards
```

## 29. SciencePortfolioDashboard

```yaml
portfolio_dashboard:
  total_cards:
  by_branch:
  by_oak_status:
  top_priority:
  top_canon_candidates:
  oak_gaps:
  high_risk_claims:
  memory_minus_triggers:
  next_actions:
  ready_for_prototype:
  ready_for_paper:
```

## 30. BranchDNA

```yaml
branch_dna_math:
  required:
    - definitions
    - axioms
    - examples
    - non_examples
    - theorem_candidates
    - counterexample_search
  promotion_to_Omega_6:
    requires:
      - proof
      - assumptions
      - edge_cases

branch_dna_physics:
  required:
    - units
    - mechanism
    - measurable_prediction
    - baseline
    - simulation_or_experiment
    - falsifier
  forbidden_without_evidence:
    - superconductivity
    - infinite energy
    - guaranteed topological phase
    - violation of conservation law

branch_dna_signals:
  required:
    - dataset
    - preprocessing
    - baseline
    - metric
    - ablation
    - robustness
    - runtime

branch_dna_ait:
  required:
    - task
    - input_output
    - evaluation_metric
    - baseline_agent
    - failure_modes
    - memory_policy
```

## 31. Anti-Hype Layer

```yaml
anti_hype_layer:
  detects:
    - proves
    - solves
    - revolutionary
    - guaranteed
    - infinite
    - absolute
    - universal
    - superconducting
    - consciousness
    - civilization-scale
  transforms:
    proves: "provides a candidate pathway to test"
    solves: "proposes a framework for"
    guaranteed: "hypothesized under conditions"
    infinite: "unbounded in the model, subject to physical limits"
    universal: "broadly applicable candidate"
    revolutionary: "potentially useful if validated"
```

```text
anti-hype != anti-ambition
anti-hype = ambition rendue publiable
```

## 32. OAK failure modes

```yaml
failure_modes:
  mathematical:
    - undefined terms
    - hidden assumptions
    - counterexample
    - non-equivalent transformation
  computational:
    - bug
    - overfitting
    - bad baseline
    - numerical instability
    - data leakage
  physical:
    - violates units
    - no mechanism
    - no measurable prediction
    - simulation artifact
    - not experimentally feasible
  epistemic:
    - high fertility confused with truth
    - metaphor treated as proof
    - name treated as object
    - result overgeneralized
```

Law:

```text
Une théorie robuste connaît ses propres façons d'échouer.
```

## 33. OAK mutation policy

```yaml
mutation_policy:
  if_test_fails:
    options:
      - lower_truth_score
      - preserve_fertility_score
      - create_residue_card
      - create_memory_minus_rule
      - split_hypothesis
      - transmute_claim
      - generate_child_hypothesis

  if_test_succeeds:
    options:
      - raise_evidence_score
      - promote_oak_status_if_gate_passed
      - create_positive_memory
      - generate_paper_seed
      - propose_reproduction_test
```

```text
Échec != fin
Échec = mutation informée
```

## 34. Hypothesis Splitter

Large claims must be factorized.

Raw claim:

```text
La FFWT-HAC-CVCD avec quaternions/octonions/sédénions détecte des phases physiques nouvelles.
```

Split:

```yaml
child_hypotheses:
  - id: ST-H-FFWT-REAL
    claim: "Real-valued FFWT features improve multi-scale signal classification."
  - id: ST-H-FFWT-COMPLEX
    claim: "Complex FFWT phase features improve oscillatory signal analysis."
  - id: ST-H-FFWT-QUAT
    claim: "Quaternionic features improve multi-axis orientation-sensitive signals."
  - id: ST-H-FFWT-OCT
    claim: "Octonionic associator features may detect higher-order coupling anomalies."
  - id: ST-H-MATERIALS
    claim: "FFWT-HAC-CVCD features may help classify material spectra."
```

Law:

```text
Une hypothèse trop grosse doit être factorisée.
```

## 35. AblationEngine

```yaml
ablation_plan:
  full_model: FFWT-HAC-CVCD
  variants:
    - real_only
    - real_plus_complex
    - real_plus_complex_plus_quaternion
    - no_cvcd
    - no_fractal_scales
    - classical_wavelet_only
  metrics:
    - accuracy
    - AUROC
    - robustness
    - runtime
    - interpretability
  decision:
    keep_component_if:
      - improves_metric
      - improves_interpretability
      - reduces_residue
```

Law:

```text
Un composant non ablaté n'est pas encore justifié.
```

## 36. DimensionCheck for physics

```yaml
dimension_check:
  equation:
  variables:
    R: ohm
    L: henry
    C: farad
    q: coulomb
    t: second
  lhs_units:
  rhs_units:
  result: pass | fail
```

RLC example:

```text
L q¨ + R q˙ + C^-1 q = V(t)
```

- `L q¨`: H · C/s² = V
- `R q˙`: Ω · A = V
- `C^-1 q`: C/F = V

Result:

```text
dimension check: pass
```

## 37. Mathematical hygiene

```yaml
math_hygiene:
  every_definition_requires:
    - domain
    - codomain
    - examples
    - non_examples
    - closure_properties
  every_theorem_requires:
    - assumptions
    - statement
    - proof_strategy
    - counterexample_search
    - edge_cases
  every_generalization_requires:
    - base_case
    - extension_rule
    - preserved_invariants
    - broken_properties

hypernumber_safety:
  required:
    - algebra_type
    - multiplication_rule
    - associativity_status
    - commutativity_status
    - norm_or_projection
    - zero_divisor_behavior
    - real_projection
```

## 38. Sedenion Safety Gate

```yaml
sedenion_gate:
  required_checks:
    - identify_zero_divisors
    - test_norm_behavior
    - preserve_real_projection
    - compare_to_complex_quaternion_baseline
    - numerical_stability
    - ablation_gain
  promotion_rule:
    can_promote_if:
      - produces unique useful feature
      - survives ablation
      - does not destabilize model
```

Law:

```text
Algèbre exotique => test encore plus strict
```

## 39. AIT Pantheon v2

```yaml
ait_pantheon:
  AIT_Capture:
    role: capture ideas and convert them into ScienceCards
  AIT_Transmuter:
    role: convert raw claims into safe testable claims
  AIT_Bayes:
    role: prioritize hypotheses
  AIT_OAKCourt:
    role: multi-role scientific review
  AIT_Prototype:
    role: generate minimal prototype plans
  AIT_Benchmark:
    role: define baselines and metrics
  AIT_MemoryMinus:
    role: detect risks and anti-rules
  AIT_ResidueMiner:
    role: transform failures into child hypotheses
  AIT_PaperForge:
    role: generate publication scaffolds
  AIT_GitHub:
    role: create PRs, issues, tests and docs
  AIT_Dashboard:
    role: report portfolio status
  AIT_Canonizer:
    role: promote, hold, split or reject cards
```

SAGE becomes:

```text
SAGE_T = Router_HGFM(⊕ AIT_i) + OAKCourt + M-
```

## 40. Ω-ST volumes

```yaml
volumes:
  I:
    title: "Manifeste des Sciences de Tristan"
    status: canon_seed
  II:
    title: "HGFM — Hypergraphes Fractals Mycéliens"
    status: formalization_needed
  III:
    title: "CVCD, LOG/EXP et Compression Fertile"
    status: prototype_needed
  IV:
    title: "Bayes-Tristan"
    status: executable_core_started
  V:
    title: "OAKCourt et Mémoire Négative"
    status: next_priority
  VI:
    title: "Mathématiques de Tristan"
    status: needs theorem hygiene
  VII:
    title: "Physique de Tristan"
    status: needs simulation gates
  VIII:
    title: "FFWT-HAC-CVCD"
    status: benchmark priority
  IX:
    title: "AIT/SAGE"
    status: agent architecture
  X:
    title: "Science OS ZÉRO-TOUCH"
    status: CLI pipeline
  XI:
    title: "Prototypes, Produits et Publications"
    status: paper/product pipeline
  XII:
    title: "Corpus vivant et Canon évolutif"
    status: long-term architecture
```

## 41. Seven supreme laws

1. Toute intuition est une graine.
2. Toute affirmation forte doit être transmutée.
3. Toute théorie doit connaître son statut.
4. Toute expérience doit produire un résidu.
5. Toute erreur devient anticorps.
6. Toute promotion doit passer une porte.
7. Le canon reste vivant.

```text
canon != dogme
canon = meilleur état validé actuel
```

## 42. Condensation

```text
Ω-ST+   = ScienceCard + Bayes-Tristan + AIT-OAK
Ω-ST++  = Ω-ST+ + ClaimTransmuter + PromotionGates + CanonScore
Ω-ST+++ = Ω-ST++ + OAKCourt + MemoryMinus + ResidueMiner
          + PrototypeContracts + ExperimentContracts + PaperForge
```

Ultimate sentence:

```text
Les Sciences de Tristan transforment toute idée en organisme scientifique évolutif, prototypable, falsifiable, mémoriel et canonisable.
```

Devise:

```text
Vision maximale. Validation maximale. Mémoire maximale. Prototype minimal. Canon vivant.
```
