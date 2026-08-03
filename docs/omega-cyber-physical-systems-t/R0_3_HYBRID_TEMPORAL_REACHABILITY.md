# Ω-CYBER-PHYSICAL-SYSTEMS-T∞ R0.3

## HybridAutomaton-T, TemporalContract-T, Reachability-T et ZenoGuard-T

Statut : `COMPUTATIONAL_RESEARCH_PROTOTYPE / NOT_FORMALLY_VERIFIED / NOT_SAFETY_CERTIFIED`

R0.3 ajoute au socle R0.1–R0.2 une couche explicite pour les systèmes qui alternent entre :

- évolution continue;
- événements discrets;
- reconfigurations;
- dérating;
- interverrouillages;
- fautes;
- replis;
- arrêts sûrs.

La couche vise les prototypes mécatroniques, robotiques, énergétiques, fluidiques, thermiques, manufacturiers et véhicules intégrés. Elle ne remplace ni un outil de vérification formelle qualifié, ni une analyse de sûreté fonctionnelle, ni des essais HIL, banc ou terrain.

---

## 1. HybridAutomaton-T

Un automate hybride R0.3 contient :

- un ensemble fini de modes;
- des variables continues;
- une dynamique affine par mode;
- des invariants de mode;
- des transitions orientées;
- des gardes;
- des resets;
- des priorités;
- un temps minimal de séjour;
- un ensemble de modes déclarés sûrs;
- un mode d’urgence optionnel.

### 1.1 Flux continus

Pour chaque variable `x_i`, un mode déclare :

```text
x_i' = b_i + Σ_j A_ij x_j
```

Cette forme est volontairement limitée et transparente. Elle permet :

- simulation déterministe;
- analyse dimensionnelle externe;
- propagation d’intervalles;
- inspection des coefficients;
- comparaison reproductible.

Elle ne prétend pas couvrir exactement toutes les dynamiques non linéaires.

### 1.2 Gardes et resets

Une transition est activée lorsque :

- toutes ses gardes sont satisfaites;
- son temps minimal de séjour est atteint;
- elle possède la meilleure priorité déterministe parmi les transitions actives.

Un reset utilise l’état avant transition :

```text
x_target := scale × x_source + offset
```

Les resets simultanés ne peuvent pas écrire deux fois dans la même variable.

### 1.3 Invariants

Les invariants sont vérifiés :

- à l’état initial;
- sur chaque échantillon;
- après chaque transition;
- dans l’exploration par intervalles.

Une violation échantillonnée reste un contre-exemple calculé. Une absence de violation ne devient pas une preuve continue.

---

## 2. Fixture électromécanique R0.3

Le fixture déterministe suit la chaîne :

```text
startup
→ tracking
→ derated
→ safe_shutdown
```

Variables :

```text
position_m
velocity_mps
temperature_k
clock_s
```

Transitions :

```text
startup-complete
thermal-derate
timed-safe-shutdown
```

Le modèle est synthétique. Les coefficients ne sont pas des paramètres de machine qualifiés.

Objectifs du fixture :

- tester les gardes;
- tester les resets d’horloge;
- tester les temps de séjour;
- tester le dérating thermique;
- tester un repli faible énergie;
- produire des témoins temporels reproductibles;
- alimenter une exploration bornée.

---

## 3. TemporalContract-T

Quatre familles sont implémentées.

### 3.1 ALWAYS

Exemple :

```text
toujours position_m <= 0.26
```

La propriété échoue dès qu’un échantillon ne satisfait pas le prédicat.

### 3.2 EVENTUALLY

Exemple :

```text
safe_shutdown est atteint avant 1.2 s
```

Une échéance optionnelle limite la recherche.

### 3.3 RESPONSE

Exemple :

```text
si temperature_k >= 303.15
alors mode = derated dans les 0.02 s
```

Chaque déclencheur observé doit posséder une réponse dans sa fenêtre.

### 3.4 MODE_SEQUENCE

Exemple :

```text
startup → tracking → derated → safe_shutdown
```

La séquence doit apparaître dans cet ordre; des échantillons intermédiaires sont permis.

### 3.5 Témoins

Chaque résultat conserve :

- première satisfaction;
- première violation;
- heure;
- mode;
- état complet;
- raison.

Frontière OAK :

```text
formal_proof: false
safety_certified: false
```

---

## 4. Reachability-T

R0.3 ajoute une exploration bornée par boîtes d’intervalles.

### 4.1 Représentation

Chaque variable possède :

```text
[borne_inférieure, borne_supérieure]
```

Les flux affines sont propagés avec arithmétique d’intervalles et Euler explicite.

### 4.2 Branches

À chaque pas :

1. propagation continue;
2. test de possibilité des invariants;
3. conservation de la branche sans transition;
4. création d’une branche pour chaque garde possiblement vraie;
5. application des resets;
6. test des invariants du mode cible;
7. déduplication déterministe.

### 4.3 États dangereux

Un prédicat dangereux est classé :

- impossible dans la boîte;
- possible;
- certain.

Le rapport sépare :

```text
unsafe_possible_count
unsafe_definite_count
```

### 4.4 Budget d’exécution

`max_nodes_per_step` borne une exécution particulière.

Il ne devient jamais une limite permanente :

```text
permanent_total_cap: null
```

Si le budget est dépassé :

```text
truncated: true
```

Une exploration tronquée ne peut pas être présentée comme complète.

### 4.5 Limites

- horizon fini;
- pas fini;
- sur-approximation par intervalles;
- pas de validated numerics;
- pas de preuve de sûreté;
- pas de garantie de complétude si tronqué;
- gardes observées aux frontières de pas.

---

## 5. ZenoGuard-T

Un cycle instantané peut provoquer une infinité théorique de transitions dans un temps fini.

R0.3 ajoute deux garde-fous calculatoires :

- nombre maximal de transitions dans un même pas;
- seuil de transitions dans une fenêtre temporelle.

Les indicateurs sont :

```text
zeno_suspected
transition_limit_hit
```

Ils ne constituent pas une preuve mathématique de comportement de Zeno. Ils empêchent la simulation de boucler silencieusement et produisent un reçu négatif.

Le fixture adversarial alterne instantanément :

```text
a → b → a → b → ...
```

La simulation doit l’arrêter et le signaler.

---

## 6. R03OAK

Le tribunal R0.3 contient douze gates :

1. structure du modèle;
2. finitude et invariants de trace;
3. séquence de transitions;
4. déterminisme de simulation;
5. contrats temporels;
6. contrôle négatif temporel;
7. reachability nominale;
8. déterminisme de reachability;
9. contrôle négatif spatial;
10. garde anti-Zeno;
11. absence de fausse certification;
12. absence de plafond permanent.

Statut attendu :

```text
CERTIFIED_COMPUTATIONAL_HYBRID_TEMPORAL_REACHABILITY_R0_3
```

Le mot `CERTIFIED_COMPUTATIONAL` signifie uniquement que les invariants logiciels déclarés du fixture ont passé la CI.

Il ne signifie pas :

- certification de sécurité;
- certification machine;
- certification véhicule;
- conformité IEC 61508, ISO 26262, DO-178C, DO-254 ou autre;
- preuve formelle;
- preuve physique;
- validation de paramètres;
- validation HIL;
- validation expérimentale.

---

## 7. Mémoire négative M⁻

R0.3 conserve quatre catégories de résultats négatifs :

### M⁻-T1 — propriété temporelle impossible

Une cible cryogénique artificielle `temperature_k <= 100` doit échouer avec témoin.

### M⁻-T2 — boîte initiale dangereuse

Une boîte qui intersecte `position_m >= 0.27` doit être marquée dangereuse possible.

### M⁻-T3 — cycle instantané

Le cycle Zeno synthétique doit être stoppé.

### M⁻-T4 — exploration tronquée

Une limite de nœuds trop faible doit rester visible comme budget d’exécution, jamais comme preuve de couverture.

---

## 8. CLI

```bash
omega-cps-r03 benchmark
omega-cps-r03 automaton-demo
omega-cps-r03 hybrid-demo --summary-only
omega-cps-r03 temporal-demo --summary-only
omega-cps-r03 reachability-demo --summary-only
omega-cps-r03 reachability-demo --adversarial --steps 2 --dt-s 0.01 --summary-only
omega-cps-r03 zeno-demo --summary-only
```

Codes de sortie :

```text
0 : propriété attendue satisfaite ou détection négative attendue réussie
2 : contre-exemple valide, bilan dangereux ou exploration tronquée
```

---

## 9. Schémas JSON

R0.3 fournit :

```text
cyber_physical_hybrid_automaton_r03.schema.json
cyber_physical_hybrid_trace_r03.schema.json
cyber_physical_temporal_report_r03.schema.json
cyber_physical_reachability_r03.schema.json
```

---

## 10. Suite R0.4

R0.4 doit préparer des adaptateurs réellement exécutables et traçables pour :

- FMI/FMU;
- Modelica;
- SPICE;
- ROS 2;
- CAN;
- OPC-UA.

Règle OAK : aucun connecteur ne sera déclaré intégré sans reçu d’exécution réel, versions, paramètres, logs, erreurs, artefacts et environnement reproductible.
