# Ω-VLA-T∞² R0.2-MAX

## Frontière générative du calcul vectoriel et de l’algèbre linéaire de Tristan

Ω-VLA-T∞² R0.2-MAX étend le noyau numérique R0.1 par une infrastructure de recherche mathématique générative, déterministe, reprenable et OAK-safe.

Le système n’impose aucune constante permanente telle que `MAX_OBJECTS = 10000`. Chaque exécution conserve cependant un budget fini, un état durable, des limites mesurées et une voie de reprise.

```text
frontière logique sans plafond arbitraire
!= calcul infini
!= ressources physiques infinies
!= vérité mathématique automatique
```

## Frontière logique exacte

La frontière est le produit de :

- 32 couches mathématiques;
- 64 programmes de recherche;
- 10 axes : scalaires, espaces, géométries, opérateurs, discrétisations, régimes, applications, questions, méthodes et statuts épistémiques.

La configuration actuelle adresse exactement :

```text
32 614 907 904 000 cellules logiques
```

Ces cellules ne sont pas créées toutes à la fois. Un index entier est converti de façon réversible en adresse structurée par codage à bases mixtes. Une progression arithmétique à pas premier avec la taille de la frontière fournit un parcours déterministe, unique et paresseux avec mémoire auxiliaire constante.

Le nombre de cellules mesure un espace de routage potentiel. Il ne mesure ni le nombre de théorèmes, ni la nouveauté, ni la vérité, ni la valeur économique.

## Pipeline MAX

```text
index logique
-> adresse réversible
-> ProblemCell falsifiable
-> hypothèses + conclusion candidate
-> invariants + baselines + méthodes + falsificateurs
-> filtre d’utilité et de risque
-> déduplication SHA-256 SQLite
-> écriture JSONL streaming
-> reçus cryptographiques
-> checkpoint atomique
-> reprise au prochain offset
-> OAKBench
```

## Modules de frontière

### `catalogs.py`

Déclare les 32 couches, les 64 programmes et les dix axes combinatoires.

### `address.py`

Encode et décode les cellules. `iter_indices(..., start_offset=...)` permet de poursuivre exactement une séquence sans permutation matérialisée.

### `models.py`

Définit les objets typés :

- `ResearchArtifact`;
- `ObjectGenome`;
- `OperatorGenome`;
- `ProblemCell`;
- `SaturationEntry`;
- `EpistemicStatus`.

Les validations empêchent une proposition générée de revendiquer automatiquement un théorème.

### `theorem_factory.py`

Compile une adresse en programme de recherche contenant :

- hypothèses explicites;
- conclusion candidate;
- invariants;
- baselines;
- méthodes;
- falsificateurs;
- artefacts attendus;
- scores de routage.

Ces scores sont des heuristiques déterministes, pas des probabilités de vérité.

### `sqlite_index.py`

Maintient un index exact de digests sur disque avec SQLite/WAL. La déduplication ne dépend plus d’un ensemble Python contenant toutes les cellules en mémoire.

### `store.py`

`StreamingShardedJSONLWriter` écrit progressivement les cellules, produit un reçu SHA-256 par shard, persiste `writer-state.json`, vérifie l’intégrité au redémarrage et refuse les shards corrompus.

### `frontier.py`

Exécute ou reprend une campagne avec :

- batch adaptatif;
- filtres de risque et d’utilité;
- SQLite hors mémoire;
- écriture streaming;
- télémétrie de batch;
- registre de saturation M−;
- checkpoints périodiques;
- reprise déterministe;
- `permanent_total_cap = null`.

## Modules mathématiques

### `spectral_dna.py`

Produit une signature numérique finie : valeurs propres, rayon et abscisse spectraux, valeurs singulières, rang numérique/effectif, conditionnement, défauts de normalité, d’hermiticité et d’unitarité, plus des sondes bornées de résolvante.

Une signature numérique n’est pas une preuve spectrale.

### `residual_intelligence.py`

Analyse les normes, l’autocorrélation, la platitude spectrale, la fréquence dominante, la sparsité et les valeurs aberrantes. Les classes obtenues servent à choisir des expériences supplémentaires; elles ne prouvent pas l’existence d’une variable physique cachée.

### `discrete_exterior.py`

Implémente des complexes de chaînes réels finis :

- validation de `B_k B_{k+1} = 0`;
- opérateurs frontière et cobord;
- Laplacien de Hodge;
- nombres de Betti;
- décomposition exacte, coexacte et harmonique;
- fixtures du cycle et du triangle rempli.

### `linearization_atlas.py`

Construit des cellules de linéarisation locale avec Jacobien, rayon, résidus mesurés, seuil de validité et graphe de recouvrement. L’atlas ne revendique aucune couverture globale automatique.

### `formal_targets.py`

Compile des cellules vers des cibles Lean 4 explicitement incomplètes. Les hypothèses naturelles restent des commentaires, `CandidateStatement` reste un placeholder et chaque preuve contient volontairement `sorry`. Les métadonnées imposent :

```text
proof_status = FORMALIZED_INCOMPLETE
formally_verified = false
theorem_claimed = false
```

## CLI

### Manifeste et inspection

```bash
omega-vla-r02 manifest
omega-vla-r02 decode 123456789
omega-vla-r02 sample --count 64 --seed 2026 --start-offset 0
```

### Première campagne finie

```bash
omega-vla-r02 campaign \
  --work-items 100000 \
  --seed 2026 \
  --initial-batch 256 \
  --min-batch 32 \
  --max-batch 8192 \
  --records-per-shard 1024 \
  --checkpoint-every-batches 1 \
  --output-dir generated/omega_vla_r02/campaign \
  --report generated/omega_vla_r02/campaign-report.json
```

### Étendre exactement la même campagne

```bash
omega-vla-r02 campaign \
  --work-items 250000 \
  --seed 2026 \
  --initial-batch 256 \
  --min-batch 32 \
  --max-batch 8192 \
  --records-per-shard 1024 \
  --output-dir generated/omega_vla_r02/campaign \
  --resume \
  --report generated/omega_vla_r02/campaign-report-250k.json
```

`--work-items` décrit la frontière finie de cette exécution. Il ne devient jamais un plafond permanent du système.

### Analyses

```bash
omega-vla-r02 benchmark --output generated/omega_vla_r02/oak.json
omega-vla-r02 spectral-dna '[[2,-1],[1,2]]'
omega-vla-r02 residual '[0,1,0,-1,0,1,0,-1]'
```

## Sorties durables

```text
generated/omega_vla_r02/campaign/
├── checkpoint.json
├── dedup.sqlite3
├── manifest.json
├── writer-state.json
└── shards/
    ├── research-cells-000000.jsonl
    ├── research-cells-000001.jsonl
    └── ...
```

Le manifeste contient le nombre de cellules, les tailles, les SHA-256 individuels, le SHA-256 agrégé et le chemin du checkpoint. Une reprise vérifie les shards et la cohérence du nombre de digests avant d’accepter de nouveaux objets.

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

L’usine génère uniquement des idées, définitions, fixtures, propositions, contre-exemples candidats ou squelettes formels incomplets. Elle ne promeut aucun objet à `FORMALLY_VERIFIED` ou `CANONICAL`.

## OAKBench

La CI Python 3.10–3.13 vérifie notamment :

- la taille et l’unicité des catalogues;
- l’aller-retour des adresses;
- l’unicité et la reprise du parcours paresseux;
- le déterminisme de l’usine et des campagnes;
- les barrières de revendication;
- la déduplication en mémoire et SQLite;
- le sharding streaming et ses hashes;
- le rejet d’un shard corrompu;
- la reprise exacte d’une campagne;
- Spectral DNA et Residual Intelligence;
- `B_k B_{k+1}=0`, Hodge et nombres de Betti;
- les atlas de linéarisation;
- les squelettes Lean explicitement incomplets;
- les trois JSON Schemas.

## Limites actuelles

La R0.2-MAX reste un noyau de recherche fini et resource-bound :

- SQLite, le disque, les quotas GitHub et les runners CI ont des limites physiques;
- la télémétrie complète dans le checkpoint peut devenir volumineuse;
- les filtres d’utilité, de nouveauté et de risque restent heuristiques;
- les sondes pseudo-spectrales ne remplacent pas une analyse certifiée;
- les diagnostics de résidus ne remplacent pas des tests statistiques adaptés;
- Hodge est actuellement réel, fini et non pondéré;
- les atlas utilisent des différences finies et des échantillons locaux;
- les fichiers Lean ne formalisent pas encore la sémantique des énoncés;
- aucune extension HGFM, FFWT, CVCD ou sédénionique n’est validée physiquement par ce dépôt.

## Roadmap R0.3+

1. file de priorité SQLite persistante;
2. reprise transactionnelle coordonnée entre shards et index après interruption au milieu d’un batch;
3. compactage et indexation Parquet/Arrow;
4. Hodge pondéré, simplicial supérieur et couplages inter-échelles;
5. comparateurs NumPy/SciPy/SymPy/JAX;
6. compilation sémantique vers Lean avec définitions fidèles;
7. unités physiques et analyse dimensionnelle;
8. atlas adaptatifs avec subdivision automatique;
9. campagnes Raman, cristaux, Maxwell, fluides, plasmas et quantique;
10. orchestration distribuée, différentielle et reproductible;
11. registre M− unifié avec Ω-SANS-PLAFOND-T∞.

## Règle OAK

```text
volume généré != connaissance
simulation != preuve
cellule logique != résultat scientifique
score de priorité != probabilité de vérité
squelette Lean avec sorry != preuve formelle
nom Tristan != loi physique
OAK_PASS != validation expérimentale
```

La valeur vient de la conversion répétée :

```text
cellule -> définition -> test -> contre-exemple
-> preuve ou réfutation -> reproduction -> application
```
