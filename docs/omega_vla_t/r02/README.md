# Ω-VLA-T∞² R0.2-MAX

## Frontière générative du calcul vectoriel et de l’algèbre linéaire de Tristan

Ω-VLA-T∞² R0.2-MAX étend le noyau numérique R0.1 par une infrastructure de
recherche générative, déterministe, reprenable et OAK-safe.

Le système n’impose aucune constante permanente du type `MAX_OBJECTS=10000`.
Chaque exécution possède néanmoins un budget fini explicite. Cette distinction
est obligatoire :

```text
frontière logique sans plafond arbitraire
!=
calcul infini
!=
ressources physiques infinies
```

Une campagne matérialise un nombre fini de cellules, mesure ses limites,
conserve un checkpoint et peut augmenter sa prochaine frontière après audit.

## Frontière logique

La frontière est le produit de :

- 32 couches mathématiques;
- 64 programmes de recherche;
- 10 axes combinatoires : scalaires, espaces, géométries, opérateurs,
  discrétisations, régimes, applications, questions, méthodes et niveaux
  épistémiques.

La configuration R0.2-MAX adresse plus de mille milliards de cellules sans les
créer toutes sur disque. Une adresse entière est convertie de façon réversible
en une cellule structurée par codage à bases mixtes.

Le nombre de cellules logiques mesure seulement l’espace de routage potentiel.
Il ne mesure ni le nombre de théorèmes, ni la valeur scientifique, ni la valeur
économique.

## Pipeline

```text
index logique
-> adresse mathématique réversible
-> ProblemCell
-> hypothèses + conclusion candidate
-> invariants + baselines + méthodes + falsificateurs
-> filtre de qualité
-> déduplication content-addressed
-> shard JSONL + SHA-256
-> checkpoint + manifeste
-> OAKBench
```

## Modules

### `catalogs.py`

Déclare les 32 couches, les 64 programmes et les axes de la frontière.

### `address.py`

Encode et décode les cellules par arithmétique à bases mixtes. Les campagnes
utilisent un itérateur déterministe sans permutation complète en mémoire.

### `models.py`

Définit :

- `ResearchArtifact`;
- `ObjectGenome`;
- `OperatorGenome`;
- `ProblemCell`;
- `SaturationEntry`;
- `EpistemicStatus`.

Le constructeur empêche une cellule générée de revendiquer un théorème sans
statut de preuve compatible.

### `theorem_factory.py`

Compile une adresse en programme de recherche falsifiable. La sortie contient :

- hypothèses;
- conclusion candidate;
- invariants;
- baselines;
- méthodes;
- falsificateurs;
- artefacts attendus;
- scores de routage.

Les scores sont des heuristiques déterministes. Ils ne sont pas des
probabilités de vérité.

### `spectral_dna.py`

Produit une signature numérique finie :

- valeurs propres;
- rayon et abscisse spectraux;
- valeurs singulières;
- rang numérique et rang effectif;
- conditionnement;
- défaut de normalité;
- défaut hermitien;
- défaut unitaire;
- sondes bornées de résolvante.

Une signature numérique n’est pas une preuve spectrale.

### `residual_intelligence.py`

Analyse les résidus par normes, autocorrélation, platitude spectrale,
fréquence dominante, sparsité et valeurs aberrantes. Les classes produites
servent à router les prochaines expériences :

- négligeable;
- sparse ou événementiel;
- corrélé;
- oscillatoire ou multi-échelle;
- lourdement distribué ou contaminé;
- approximativement non structuré.

Le moteur ne conclut pas automatiquement à une nouvelle variable physique.

### `frontier.py`

Exécute une campagne finie avec :

- batch adaptatif;
- filtres de risque et d’utilité;
- déduplication;
- télémétrie;
- registre de saturation M−;
- absence explicite de plafond total permanent.

### `store.py`

Écrit des shards JSONL, des reçus SHA-256, un checkpoint atomique et un
manifeste agrégé.

### `oak_max.py`

Vérifie :

- la forme des catalogues;
- l’aller-retour des adresses;
- le déterminisme de l’usine;
- l’absence de revendications indues;
- le déterminisme des campagnes;
- la séparation entre budget fini et plafond permanent;
- les fixtures Spectral DNA;
- les fixtures Residual Intelligence.

## CLI

### Manifeste

```bash
omega-vla-r02 manifest
```

### Décoder une cellule

```bash
omega-vla-r02 decode 123456789
```

### Générer quelques cellules

```bash
omega-vla-r02 sample --count 64 --seed 2026 --output generated/sample.json
```

### Campagne finie et shardée

```bash
omega-vla-r02 campaign \
  --work-items 100000 \
  --seed 2026 \
  --initial-batch 256 \
  --min-batch 32 \
  --max-batch 8192 \
  --records-per-shard 1024 \
  --output-dir generated/omega_vla_r02/campaign-100k \
  --report generated/omega_vla_r02/campaign-100k-report.json
```

`--work-items 100000` décrit cette expérience seulement. Ce nombre n’est pas
un plafond permanent du système.

### OAKBench

```bash
omega-vla-r02 benchmark --output generated/omega_vla_r02/oak.json
```

### Spectral DNA

```bash
omega-vla-r02 spectral-dna '[[2,-1],[1,2]]'
```

### Intelligence des résidus

```bash
omega-vla-r02 residual '[0,1,0,-1,0,1,0,-1]'
```

## Fichiers produits par une campagne

```text
generated/omega_vla_r02/campaign/
├── checkpoint.json
├── manifest.json
└── shards/
    ├── research-cells-000000.jsonl
    ├── research-cells-000001.jsonl
    └── ...
```

Le manifeste contient :

- nombre de cellules acceptées;
- nombre de shards;
- nombre d’octets;
- SHA-256 de chaque shard;
- SHA-256 agrégé;
- chemin du checkpoint.

## Statuts épistémiques

```text
IDEA
DEFINED
NUMERICALLY_OBSERVED
COUNTEREXAMPLE_FOUND
PROPOSITION
PROVED_BY_HAND
FORMALIZED_INCOMPLETE
FORMALLY_VERIFIED
REPRODUCED
CANONICAL
```

R0.2-MAX génère par défaut des idées, définitions, fixtures, propositions,
contre-exemples candidats ou squelettes formels incomplets. Il ne promeut pas
un objet à `FORMALLY_VERIFIED` ou `CANONICAL`.

## Limites actuelles

La R0.2-MAX est un noyau de recherche logicielle, pas une plateforme infinie.
Ses limites présentes doivent être mesurées :

- la déduplication exacte en mémoire doit devenir SQLite ou disque-backed pour
  des campagnes très grandes;
- la liste des cellules acceptées est encore conservée en mémoire avant écriture
  des shards;
- le filtrage de qualité est heuristique;
- le pseudo-spectre est un ensemble fini de sondes et non un calcul certifié;
- l’analyse des résidus ne remplace pas un test statistique adapté;
- aucune sortie n’est automatiquement compilée en Lean, Coq ou Isabelle;
- aucune extension HGFM, FFWT ou sédénionique n’est validée par ce dépôt.

Ces limites sont des entrées de roadmap et non des détails à masquer.

## Roadmap R0.3+

1. index de déduplication SQLite hors mémoire;
2. écriture de shards réellement streaming;
3. reprise depuis checkpoint avec continuation exacte de la séquence;
4. file de priorité persistante;
5. comparateur de baselines NumPy/SciPy/SymPy/JAX;
6. compilateur de cibles Lean;
7. atlas de linéarisations locales;
8. Hodge simplicial pondéré;
9. unités physiques et analyse dimensionnelle;
10. campagnes Raman, cristaux, Maxwell, fluides et plasmas;
11. orchestration distribuée et différentielle;
12. registre M− unifié avec Ω-SANS-PLAFOND-T∞.

## Règle OAK

```text
volume généré != connaissance
simulation != preuve
cellule logique != résultat scientifique
score de priorité != probabilité de vérité
nom Tristan != loi physique
OAK_PASS != validation expérimentale
```

La valeur du système dépend de la conversion répétée :

```text
cellule
-> définition
-> test
-> contre-exemple
-> preuve ou réfutation
-> reproduction
-> application
```
