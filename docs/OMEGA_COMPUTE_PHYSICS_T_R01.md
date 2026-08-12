# Ω-COMPUTE-PHYSICS-T∞ / Ω-COMPLEXITY-ATLAS-T∞ — R0.1

## Statut

**Prototype computationnel OAK-safe.** Cette branche mesure et ajuste des lois empiriques de ressources sur des domaines finis. Un ajustement `T ~= c n^p` ne constitue jamais, à lui seul, une preuve de `T in Theta(n^p)`.

## Phrase mère

> Un programme possède une géométrie mesurable de ressources. Cette géométrie peut être observée, compressée en lois empiriques, différenciée, composée, falsifiée, puis utilisée pour prédire et optimiser l'exécution sous contraintes.

Le Big-O théorique est une projection asymptotique importante, mais il ne décrit ni les constantes, ni les transitions cache/RAM/VRAM, ni la contention, ni les coûts de transfert, ni l'incertitude expérimentale. Ω-COMPUTE-PHYSICS-T∞ conserve explicitement ces couches séparées.

---

## 1. Objet canonique

Pour une fonction ou un pipeline `F`, on définit un état computationnel

```text
x_F = (dimensions, sparsity, rank, dtype, batch, threads, device, ...)
```

et un vecteur/tensor de ressources

```text
R_F = (
  wall_time,
  cpu_time,
  gpu_time,
  RAM,
  VRAM,
  FLOPs,
  cache_misses,
  bytes_read,
  bytes_written,
  IO,
  network,
  energy,
  monetary_cost,
  quality,
  failure_risk,
  ...
)
```

R0.1 implémente le sous-ensemble portable suivant :

- `wall_time_s` via `time.perf_counter` ;
- `cpu_time_s` via `time.process_time` ;
- `peak_python_bytes` et `final_python_bytes` via `tracemalloc` ;
- provenance machine Python standard-library ;
- ressources arbitraires fournies par des adaptateurs futurs.

**Important :** `peak_python_bytes` n'est pas le RSS total, la VRAM ni la mémoire du système. Cette sémantique est inscrite dans la provenance de chaque mesure.

---

## 2. ResourceSample et Atlas vivant

Chaque exécution devient un point :

```text
ResourceSample(
  variables = {a, b, c, ...},
  resources = {T, M, E, ...},
  metadata = {machine, software, commit, campaign, ...}
)
```

L'Atlas contient les mesures et plusieurs modèles concurrents conditionnés par ressource.

```text
program
  -> measurement campaign
  -> ResourceSamples
  -> candidate feature library
  -> empirical resource model
  -> local geometry
  -> OAK certificate
  -> atlas.json
```

---

## 3. Lois multivariées

Pour `F(A,B,C)` avec tailles `a,b,c`, le premier objet n'est plus seulement `O(n^p)` mais une surface :

```text
T = f(a,b,c)
```

R0.1 construit une bibliothèque bornée de primitives :

- constante ;
- monômes multivariés jusqu'à un degré total configurable ;
- `log(x)` ;
- `x log(x)`.

Exemple de famille candidate :

```text
1, a, b, c, a^2, ab, ac, b^2, bc, c^2,
log(a), log(b), log(c), a log(a), b log(b), c log(c)
```

Puis le moteur ajuste

```text
R_hat(x) = sum_k theta_k phi_k(x)
```

avec régularisation faible et certificat (`domain`, `n_samples`, `RMSE`, `R²`, statut épistémique).

### Anti-explosion

La génération de transformations est combinatoire. R0.1 impose donc `max_features`. Les futures versions utiliseront sélection active, sparsité, MDL/CVCD et recherche de représentations plutôt qu'une expansion aveugle.

---

## 4. Scaling Field / Complexity Jacobian

Le champ local d'élasticité est

```text
kappa_i(x) = d log R / d log x_i
```

Si localement

```text
R ~= C a^p b^q c^r
```

alors

```text
kappa ~= (p,q,r)
```

Le prototype calcule ces exposants par différence finie sur le modèle ajusté.

Pour plusieurs ressources, la généralisation naturelle est le Jacobien

```text
J_ij = d log R_i / d log x_j
```

qui transforme une fonction en carte locale « variable -> ressource ».

---

## 5. Interaction Hessian

La dérivée seconde

```text
H_ijk = d² log R_i / (d log x_j d log x_k)
```

mesure comment la sensibilité à une variable change lorsqu'une autre variable change. Elle détecte des interactions qui disparaissent dans un Big-O scalaire.

R0.1 expose `interaction_hessian()` pour une ressource à la fois.

---

## 6. Tous les chemins de changement d'échelle

Au lieu de forcer

```text
(a,b,c) -> (lambda a, lambda b, lambda c)
```

on autorise la direction

```text
(a,b,c) -> (lambda^u a, lambda^v b, lambda^w c)
```

Le champ local donne alors immédiatement

```text
p(u,v,w) = u*kappa_a + v*kappa_b + w*kappa_c
```

R0.1 l'implémente via `path_scaling_exponent()`.

Cela distingue proprement des chemins asymptotiques multivariés différents.

---

## 7. Diagrammes de phases computationnelles

Un même ordre asymptotique peut traverser plusieurs régimes réels :

```text
L1/L2/L3 cache -> RAM -> NUMA -> swap -> OOM
CPU compute-bound <-> memory-bound
GPU compute -> VRAM pressure -> host/device transfers
local IO -> network congestion
```

R0.1 fournit un détecteur volontairement simple : sur une tranche 1-D contrôlée, il compare les pentes log-log adjacentes et émet des objets

```text
status = empirical-regime-candidate
```

Une frontière détectée n'est pas automatiquement attribuée au cache, au GPU ou à un mécanisme particulier : cette causalité exige télémétrie ou expérience supplémentaire.

---

## 8. HGFM : coût des nœuds ET des hyperarêtes

Le modèle cible est un hypergraphe récursif :

```text
repo
  -> package
    -> pipeline
      -> function
        -> block
          -> operation
```

Chaque nœud porte une loi de ressources. Les arêtes portent aussi un coût :

```text
transfer, serialization, copy, buffer, sync, network
```

Ainsi :

```text
system_cost != sum(function_costs)
```

Les futures versions calculeront des chemins critiques distincts pour le temps, la mémoire, l'énergie et le coût.

---

## 9. Complexity-IR et Program Genome

La cible R0.2+ est un IR matériellement neutre :

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
WRITE
```

avec volumes et motifs d'accès. Un `ProgramGenome` sera composé avec un `MachineGenome` :

```text
ProgramGenome x MachineGenome -> distribution de ressources
```

Objectif : transfert de modèles entre machines avec incertitude explicitement quantifiée.

---

## 10. Machine Genome

Le génome cible inclut :

```text
cores
vector_width
clock regimes
cache hierarchy
memory bandwidth/latency
GPU compute
VRAM
PCIe/interconnect
disk
network
thermal/power regimes
```

R0.1 ne prétend pas inférer ces grandeurs. Il enregistre seulement une empreinte de provenance portable. Des microbenchmarks calibrés et adaptateurs système viendront ensuite.

---

## 11. Resource Contracts

Une fois un modèle validé dans son domaine, on peut poser :

```text
T(x) <= 10 s
M(x) <= 8 GiB
```

`resource_contract()` produit un contrôle conditionné au modèle. Le contrat porte toujours l'avertissement que sa validité dépend du domaine mesuré et de la machine/configuration.

---

## 12. Problème inverse

La direction plus forte est :

```text
budget -> configuration
```

et non seulement

```text
configuration -> coût
```

Cible :

```text
argmax quality(x, algorithm, hardware)
subject to
  time <= T_max
  memory <= M_max
  energy <= E_max
  cost <= C_max
```

Cette couche deviendra `BudgetCompiler-T` et `ParetoAtlas-T`.

---

## 13. Active Benchmarking

Un grid search de `m` valeurs sur `n` variables coûte `m^n`. La version avancée choisira les prochains points selon :

```text
information gain / benchmark cost
```

Priorités :

1. régions d'incertitude élevée ;
2. frontières de régime ;
3. points qui discriminent des lois concurrentes ;
4. régions réellement utiles au workflow ;
5. contre-exemples maximisant le résidu.

Cela transforme le profiling en expérimentation active.

---

## 14. CVCD / variables naturelles

Le but n'est pas d'accumuler des milliers de termes. Le but est de découvrir les coordonnées qui compressent la loi.

Exemple : si

```text
T(a,b,c,d) ~= alpha * a*b*c/d
```

chercher

```text
u = a*b*c/d
```

puis réduire à

```text
T ~= alpha*u
```

La cible `Compute-CVCD` optimise conjointement erreur prédictive, complexité de représentation et stabilité hors échantillon.

---

## 15. Complexity Proof Ladder

Les statuts doivent rester séparés :

| Niveau | Signification |
|---|---|
| L0 | intuition / hypothèse |
| L1 | fit in-sample |
| L2 | validation hors échantillon |
| L3 | reproduction multi-machine / multi-run |
| L4 | explication algorithmique |
| L5 | borne mathématique démontrée |
| L6 | preuve formelle/kernel-acceptée |

R0.1 produit des objets **empirical-fit**. Le texte « Big-O prouvé » est interdit pour un fit seul.

---

## 16. M- / résidus

Chaque écart

```text
residual = observed - predicted
```

est une donnée fertile. Les futures campagnes stockeront les gros résidus dans M- avec leur contexte : commit, machine, versions, variables, télémétrie et cause confirmée ou inconnue.

Candidats : cache, NUMA, garbage collection, contention, throttling, réseau, fragmentation, changement de code, extrapolation, mauvais choix de variables.

---

## 17. Git / Complexity Diff

Cible CI : chaque commit possède une signature de ressources. Une PR pourra produire :

```text
COMPLEXITY DIFF
foo()
  runtime median: -18%
  peak memory: +7%
  empirical exponent: 1.02 -> 1.98
  crossover: candidate near n ~= 740
  confidence/domain: ...
```

Une régression de loi d'échelle est plus importante qu'une simple constante locale et doit être détectable séparément.

---

## 18. Arbre R0.1

```text
omega_compute_physics_t/
  __init__.py
  atlas.py
  profiler.py
  cli.py

tests/
  test_omega_compute_physics_t.py

docs/
  OMEGA_COMPUTE_PHYSICS_T_R01.md

complexity_atlas/
  schema_v0_1.json

.github/workflows/
  omega-compute-physics.yml
```

CLI :

```bash
python -m omega_compute_physics_t.cli demo \
  --output artifacts/compute-atlas/demo.json
```

Fit d'un jeu de mesures JSONL :

```bash
python -m omega_compute_physics_t.cli fit-jsonl samples.jsonl \
  --target wall_time_s \
  --degree 2 \
  --output artifacts/compute-atlas/atlas.json
```

---

## 19. Roadmap cristallisée

### R0.1 — livré dans cette branche

- ResourceSample ;
- profiler stdlib ;
- pipeline séquentiel ;
- polynômes multivariés + log + xlogx ;
- certificat OAK ;
- élasticité locale ;
- Hessien d'interaction ;
- direction de scaling ;
- frontière de régime empirique ;
- Resource Contract ;
- Atlas JSON ;
- tests + CI.

### R0.2

- séparation train/validation automatique ;
- AIC/BIC/MDL et sélection parcimonieuse ;
- modèles concurrents + posterior ;
- incertitude prédictive ;
- détection de dérive ;
- commit/provenance Git complète ;
- Complexity Diff.

### R0.3

- DAG pipelines ;
- coûts d'arêtes ;
- chemins critiques temps/mémoire ;
- scheduler/contention model ;
- phase diagrams multidimensionnels ;
- active benchmarking.

### R0.4

- MachineGenome calibré ;
- perf counters / RSS / RAPL / GPU adapters ;
- Complexity-IR ;
- cross-hardware transfer.

### R0.5+

- Compute-CVCD ;
- symbolic regression contrainte ;
- counterfactual twin ;
- Pareto Atlas ;
- Budget Compiler ;
- Resource-Aware Agent Planning ;
- observation -> conjecture de complexité -> Ω-FORMAL-PROOF-T∞.

---

## 20. Dashboard canonique

| Axe | R0.1 |
|---|---|
| Vérité | prototype empirique, lois théoriques non revendiquées |
| Code | noyau Python stdlib |
| Test | régressions synthétiques + profiler/pipeline |
| Produit | profiler/atlas prédictif pour CI, science et agents |
| IP | à classifier avant publication de mécanismes distinctifs supplémentaires |
| GitHub | branche dédiée + PR |
| Revenu | futur service CI/performance, SDK, audit, scheduling |
| Risque M- | surfit, faux Big-O, télémétrie incomplète, extrapolation |
| Prochaine action | valider CI puis R0.2 validation/incertitude/Complexity Diff |

## Règle finale OAK

```text
measured scaling != asymptotic proof
correlation != causal mechanism
model interpolation != safe extrapolation
node costs alone != pipeline cost
single-machine result != hardware-independent law
```

La cible est donc une **science du coût computationnel vérifiable**, pas un vocabulaire physique plaqué sur des benchmarks.
