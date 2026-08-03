# Ω-SUITE-FORM-T∞ R∞ — Genesis Pack

## Statut

Ω-SUITE-FORM-T∞ R∞ est un système de recherche computationnelle pour découvrir,
relier, comparer et falsifier des représentations analytiques de suites finies.

Il ne prétend pas qu’un préfixe fini identifie une suite infinie unique. Tous les
reçus produits automatiquement conservent :

```json
{
  "global_identity_proved": false,
  "formal_proof_completed": false
}
```

Une promotion à OAK-5 exige une preuve mathématique globale explicite. Une
promotion à OAK-6 exige une preuve formelle terminée, sans `sorry`, `admit`,
axiome ad hoc ou autre placeholder.

---

## 1. Changement d’échelle

R0.1 couvre trois représentations :

1. polynôme de Newton;
2. récurrence linéaire à coefficients constants;
3. fonction génératrice rationnelle correspondante.

R∞ ajoute une architecture extensible :

- 256 familles analytiques canoniques;
- 512 transformations canoniques;
- 1 024 anti-motifs M⁻;
- 128 classes de validation;
- 64 régimes;
- 32 domaines de données;
- 34 359 738 368 cellules logiques adressables.

Le nombre de cellules est :

```text
256 × 512 × 128 × 64 × 32 = 34 359 738 368
```

Ces cellules ne sont pas toutes copiées dans Git. Elles sont accessibles par un
adressage déterministe et matérialisées par campagnes finies, selon le budget
disponible.

Exemple d’adresse :

```text
f007.t143.v012.r03.d05
```

L’absence de plafond permanent signifie :

- aucune constante globale ne limite définitivement la recherche;
- une exécution donnée reste finie et traçable;
- les limites opérationnelles peuvent porter sur le temps, la mémoire, le
  stockage, le calcul ou le nombre de cellules matérialisées par campagne;
- une campagne suivante peut reprendre avec un budget supérieur.

---

## 2. Noyau typé

### `CellAddress`

Coordonnées :

```text
family
transformation
validator
regime
domain
```

Propriétés :

- sérialisation canonique;
- parsing strict;
- hash SHA-256;
- conversion indice plat ↔ adresse;
- vérification de domaine.

### `AnalyticFamily`

Chaque famille porte :

- identifiant stable;
- classe analytique;
- représentation;
- détecteurs;
- compilateurs;
- invariants;
- obligations de preuve;
- risques;
- maturité;
- capacité exacte;
- capacité multivariée.

### `TransformationSpec`

Chaque transformation porte :

- source et cible;
- conditions d’exactitude;
- obligations de preuve;
- risques;
- invertibilité;
- perte éventuelle;
- maturité.

### `FormCandidateRInf`

Chaque candidat conserve :

- famille;
- expression;
- paramètres;
- hypothèses;
- niveau OAK;
- concordance observée;
- prédiction retenue;
- validation adversariale;
- complexité;
- résidu;
- obligations de preuve;
- risques;
- preuves;
- statut de preuve globale et formelle.

---

## 3. Catalogue 256 familles

Les 256 familles proviennent de 32 graines analytiques croisées avec huit
régimes de données :

```text
scalar_exact
scalar_noisy
vector_exact
multivariate_exact
modular
symbolic_parameter
piecewise
asymptotic_residual
```

Les 32 graines sont :

1. polynôme de Newton;
2. quasi-polynôme;
3. fonction rationnelle de l’indice;
4. exponentielle-polynomiale;
5. récurrence constante;
6. suite P-récursive;
7. suite hypergéométrique;
8. suite q-hypergéométrique;
9. fonction génératrice ordinaire rationnelle;
10. fonction génératrice algébrique;
11. fonction génératrice D-finie;
12. fonction différentiellement algébrique;
13. fonction génératrice exponentielle;
14. série de Dirichlet;
15. suite multiplicative;
16. convolution de Dirichlet;
17. suite automatique;
18. suite k-régulière;
19. suite morphique;
20. récurrence non linéaire;
21. lift de Koopman/Carleman;
22. suite de moments;
23. polynômes orthogonaux;
24. fraction continue;
25. représentation intégrale;
26. représentation Mellin/Laplace;
27. asymptotique classique;
28. transsérie;
29. processus stochastique;
30. suite matricielle ou tensorielle;
31. fonction génératrice multivariée;
32. description algorithmique.

Cette factorisation évite de maintenir 256 modules presque identiques. Chaque
entrée reste cependant matérialisable en JSONL avec un identifiant et un digest
stables.

---

## 4. Catalogue 512 transformations

Les transformations sont produites à partir de 64 graines canoniques et huit
modes :

```text
forward
inverse
restricted
multivariate
modular
symbolic
numerical_guarded
residual_aware
```

Les transformations couvrent notamment :

- décalage et décimation;
- différences et sommes partielles;
- transformée binomiale;
- inversion de Möbius;
- convolutions de Cauchy et Dirichlet;
- compilation récurrence ↔ fonction génératrice;
- P-récursif ↔ D-fini;
- rapport hypergéométrique ↔ Gamma/Pochhammer;
- Prony et rang de Hankel;
- transformée en Z;
- Borel, Mellin et Laplace;
- extraction de coefficients;
- réversion et inversion de Lagrange;
- diagonales multivariées;
- TensorProdLift-T et Koopman;
- extraction récursive des résidus;
- factorisation d’opérateurs d’Ore;
- analyse de singularités;
- Richardson;
- projection modulaire, CRT et reconstruction rationnelle;
- PSLQ gardé par précision;
- FFT, ondelettes et FFWT;
- moments et fractions continues;
- sélection active d’indices;
- recherche de contre-exemples;
- squelettes d’induction et export formel;
- mise à jour Bayes-Tristan;
- classement MDL et Pareto;
- segmentation et mélanges;
- quotient par symétrie;
- round-trip de représentations;
- oracle interlangage;
- certification par intervalles;
- tests génératifs et mutationnels;
- provenance et chaînes de reçus;
- compression LOG/EXP;
- extraction CVCD;
- OAKGate;
- mise à jour M⁻.

Trois graines secondaires restent dans le code comme backlog expérimental mais
ne consomment pas d’indices canoniques R∞ :

```text
normalize_scale
unit_check
noether_residue
```

Cette décision conserve CVCD, OAK et M⁻ dans les 64 graines canoniques.

---

## 5. Catalogue M⁻ de 1 024 anti-motifs

Seize anti-motifs fondamentaux sont croisés avec huit contextes et huit
mutations :

```text
16 × 8 × 8 = 1 024
```

Anti-motifs fondamentaux :

- interpolation vide;
- mémorisation par récurrence d’ordre élevé;
- promotion numérique vers exact;
- asymptotique présentée comme égalité;
- recherche finie présentée comme preuve;
- branche analytique non déclarée;
- erreur de domaine;
- dérive d’origine des indices;
- période aliasée par fenêtre courte;
- faux positif modulaire;
- hallucination de précision;
- annulateur non minimal;
- singularité apparente mal interprétée;
- échange illégal limite/somme/intégrale;
- placeholder formel présenté comme preuve;
- mélange non identifiable.

Contextes :

```text
exact_integer
exact_rational
floating_point
complex
multivariate
modular
asymptotic
formal_bridge
```

Mutations :

```text
base
boundary
remote_index
precision
subsequence
parameter
multimodel
roundtrip
```

Chaque entrée M⁻ fournit :

- détecteur;
- contre-vérification;
- gravité;
- plafond de promotion OAK;
- explication;
- identifiant stable.

---

## 6. Nouveaux détecteurs exacts

### 6.1 Quasi-polynômes

Forme :

```text
a_n = P_r(n), n ≡ r (mod m)
```

Algorithme :

1. essayer une période candidate `m`;
2. séparer les sous-suites par classe de résidu;
3. exprimer chaque sous-suite dans la base binomiale de Newton;
4. refuser l’interpolation vacue;
5. tester les termes retenus;
6. classer par période, degré et complexité.

Le détecteur ne prétend pas que la période continue globalement sans preuve.

### 6.2 Fonctions rationnelles de l’indice

Forme :

```text
a_n = P(n) / Q(n)
```

Normalisation R∞ :

```text
Q(0) = 1
```

Les inconnues sont résolues par Gauss-Jordan rationnel exact. Le système doit
être surdéterminé. Les singularités sur les indices observés entraînent le
rejet.

### 6.3 Suites hypergéométriques

Forme :

```text
a_(n+1) / a_n = R(n)
```

Le rapport est ajusté comme fonction rationnelle exacte puis recompilé en
produit :

```text
a_n = a_0 ∏_(k=0)^(n-1) R(k)
```

La première version refuse explicitement les zéros, plutôt que de diviser
silencieusement par zéro. Une future version segmentera les zéros et leurs
multiplicités.

### 6.4 Suites P-récursives

Forme :

```text
Σ_(j=0)^r p_j(n) a_(n+j) = 0
```

Le problème homogène est traité par normalisation successive d’un coefficient.
Pour chaque pivot :

1. fixer le coefficient à 1;
2. résoudre exactement le système surdéterminé restant;
3. substituer l’opérateur sur toutes les équations d’entraînement;
4. tester les équations retenues;
5. dédupliquer les opérateurs;
6. classer par ordre, degré et complexité.

La sortie reste une conjecture d’annulateur sur préfixe fini.

---

## 7. Sélection active des indices

Plusieurs candidats peuvent partager tous les termes observés. R∞ évalue leurs
prédictions sur une frontière d’indices et cherche les indices maximisant :

- entropie des prédictions;
- nombre de valeurs distinctes;
- désaccords par paires;
- étendue numérique;
- erreurs de domaine.

Le système peut ainsi recommander `n=257` plutôt que les seuls indices
consécutifs suivants.

Une frontière géométrique combine :

- une zone dense près du préfixe;
- des indices doublés;
- les voisins `n-1`, `n`, `n+1` de chaque échelle.

---

## 8. Campagnes adaptatives

Une campagne possède un budget fini :

```text
wall_time_seconds
memory_megabytes
storage_megabytes
compute_units
materialized_cell_cap
minimum_marginal_value
minimum_value_cost_ratio
```

`materialized_cell_cap` est une limite optionnelle de campagne, pas un plafond
permanent du système.

Chaque cellule reçoit une estimation :

```text
novelty
evidence_gain
coverage_gain
counterexample_gain
estimated_cost
risk
dependencies_ready
```

Valeur marginale :

```text
max(0, novelty + evidence_gain + coverage_gain + counterexample_gain - risk)
```

Ratio :

```text
marginal_value / estimated_cost
```

La frontière est une file de priorité. Lorsqu’une cellule fertile est acceptée,
ses voisines sont ajoutées. La campagne s’arrête pour une raison explicite :

- budget temps;
- budget calcul;
- limite de matérialisation de campagne;
- prochaine cellule trop coûteuse;
- seuil de valeur marginale;
- seuil valeur/coût;
- frontière épuisée.

---

## 9. Matérialisation

### Catalogue

```bash
omega-sequence-forms-rinf materialize out --cells 100000
```

Produit :

```text
out/catalog.jsonl
out/cells.jsonl
```

Le catalogue contient 1 792 lignes :

```text
256 + 512 + 1 024 = 1 792
```

Les cellules sont écrites en flux. La mémoire ne dépend pas du nombre total de
cellules logiques.

Chaque reçu contient :

- nombre de lignes;
- nombre d’octets;
- temps;
- SHA-256;
- raison d’arrêt;
- chemin;
- budget;
- seed;
- taille logique;
- taille matérialisée;
- absence de plafond permanent;
- absence de preuve globale.

---

## 10. CLI

### Catalogue

```bash
omega-sequence-forms-rinf catalog
omega-sequence-forms-rinf catalog --records --output catalog.json
```

### Espace logique

```bash
omega-sequence-forms-rinf space --sample 32 --seed 42
```

### Découverte

```bash
omega-sequence-forms-rinf discover \
  "1,1,2,6,24,120,720,5040,40320,362880,3628800,39916800"
```

Limiter les familles :

```bash
omega-sequence-forms-rinf discover "..." \
  --families hyper prec \
  --max-degree 6 \
  --max-order 6
```

### Benchmark

```bash
omega-sequence-forms-rinf benchmark --campaign-cells 512 --seed 314159
```

### Campagne

```bash
omega-sequence-forms-rinf campaign \
  --campaign-id first-rinf \
  --cells 100000 \
  --compute-units 500000 \
  --minimum-ratio 0.2
```

### Matérialisation

```bash
omega-sequence-forms-rinf materialize generated/rinf \
  --cells 1000000 \
  --storage-mb 2048 \
  --compute-units 2000000
```

---

## 11. OAK

Niveaux :

| Niveau | Nom | Exigence minimale |
|---:|---|---|
| 0 | VISUAL_PATTERN | motif descriptif |
| 1 | OBSERVED_FIT | accord observé et domaine déclaré |
| 2 | HELD_OUT_PREDICTION | prédiction retenue complète |
| 3 | ADVERSARIAL_VALIDATION | indices éloignés, mutations et concurrents |
| 4 | SYMBOLIC_IDENTITY | substitution symbolique et singularités |
| 5 | MATHEMATICAL_PROOF | argument global complet |
| 6 | FORMAL_PROOF | assistant de preuve, aucun placeholder |

Le `PromotionDecision` rapporte :

- niveau demandé;
- niveau accordé;
- vérifications manquantes;
- risques bloquants;
- anti-motifs bloquants;
- nombre de preuves;
- nombre de provenances indépendantes;
- raisons.

---

## 12. Benchmark R∞

Fixtures principales :

- quasi-polynôme période 3, degré 3;
- rationnelle \(P_2/Q_1\);
- factorielle;
- coefficient binomial central;
- annulateur P-récursif de la factorielle;
- quasi-polynôme brisé en fin de préfixe;
- hypergéométrique brisée en fin de préfixe.

Le benchmark vérifie aussi :

- cardinalités de catalogue;
- 34 359 738 368 cellules logiques;
- campagne déterministe;
- absence de preuve globale;
- digest déterministe.

Le flux synthétique est illimité :

```python
from omega_sequence_forms_t.rinf.benchmark import synthetic_fixture_stream

stream = synthetic_fixture_stream(seed=11)
for _ in range(1_000_000):
    descriptor = next(stream)
```

Il alterne :

- quasi-polynomial;
- rational-index;
- hypergeometric;
- P-recursive.

---

## 13. Tests

Le fichier `tests/test_omega_sequence_forms_rinf.py` couvre :

- 256 familles;
- 512 transformations;
- 1 024 anti-motifs;
- unicité des identifiants;
- présence de CVCD/OAK/M⁻;
- adressage et round-trip;
- permutation Feistel;
- échantillonnage sans allocation massive;
- sharding;
- quasi-polynômes;
- rationnelles;
- hypergéométriques;
- P-récursives;
- mutations adversariales;
- sélection active;
- promotion OAK;
- graphe de preuves;
- mémoire négative;
- delta-debugging;
- campagnes;
- matérialisation;
- flux de 10 000 fixtures;
- benchmark complet;
- déterminisme.

---

## 14. CI

Le workflow `omega-sequence-forms-rinf.yml` :

1. compile le package;
2. exécute les tests sur Python 3.10 à 3.13;
3. exécute deux benchmarks déterministes;
4. compare leurs octets;
5. matérialise 100 000 cellules;
6. vérifie le nombre de lignes;
7. produit un reçu;
8. téléverse les JSONL comme artefact GitHub Actions.

Le workflow ne fusionne rien et ne publie aucune affirmation mathématique.

---

## 15. Limites actuelles

R∞ Genesis implémente réellement quatre nouveaux détecteurs. Les autres familles
du catalogue sont des spécifications adressables jusqu’à implémentation et
validation.

Non encore implémentés :

- q-hypergéométrique;
- automatique et k-régulier;
- morphique;
- fonction génératrice algébrique;
- D-finie complète;
- algèbre d’Ore avancée;
- factorisation d’opérateurs;
- moments et mesures;
- fractions continues;
- asymptotique par singularités;
- transséries;
- TensorProdLift-T;
- backend Rust/C++;
- preuve Lean/Coq/Isabelle.

La présence d’une cellule ou d’une famille dans le catalogue ne signifie pas
qu’elle est implémentée, prouvée ou validée expérimentalement.

---

## 16. Prochain front R∞

Ordre recommandé :

1. corriger toute défaillance CI;
2. ajouter rang de Hankel exact et Prony;
3. compiler P-récursif ↔ D-fini;
4. ajouter rapports q-hypergéométriques;
5. ajouter automates et noyaux k;
6. ajouter graphe de représentations;
7. ajouter résidualisation récursive;
8. ajouter backend Rust;
9. ajouter oracle Python–Rust;
10. ajouter export Lean de certificats sans placeholder.

---

## Invariant final

> Une formule issue d’un préfixe fini est un mécanisme candidat. Le volume de
> calcul, le nombre de cellules, l’élégance symbolique ou l’accord sur des
> millions de termes ne remplacent jamais une preuve globale.
