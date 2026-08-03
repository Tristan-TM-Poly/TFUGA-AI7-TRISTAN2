# Ω-POLYGLOT-MULTIVERSE-T∞ R0.2

R0.2 transforme le laboratoire R0.1 en une architecture générative, adressable et checkpointée pour conserver simultanément des implémentations Python, C, C++ et Rust, sans prétendre qu’un langage est universellement supérieur.

## Échelle vérifiable

Le catalogue canonique contient 1 024 `AlgorithmSpec`. Chaque algorithme est croisé avec :

- 4 langages;
- 16 stratégies;
- 5 précisions;
- 8 organisations mémoire;
- 8 régimes de parallélisme;
- 16 profils matériels;
- 8 objectifs.

Cela donne 2 621 440 variantes logiques par algorithme et 2 684 354 560 cellules logiques pour le catalogue initial. Ces cellules ne sont pas déclarées compilées, testées ou scientifiquement validées. Elles constituent une frontière adressable en mémoire constante.

## Objets livrés

- `AlgorithmSpec` et contrat numérique typé;
- identifiants déterministes fondés sur SHA-256;
- IR auditable avec obligations de preuve;
- frontière mixte-radix à accès aléatoire;
- générateurs Python, C, C++ et Rust pour le kernel affine certifié;
- `PolicyGate` statique pour éliminer les combinaisons incohérentes;
- campagnes shardées, checkpointées et reprenables;
- sélection Pareto et pondérée;
- empreinte matérielle prudente;
- registre append-only M⁺/M⁻;
- matérialiseur déterministe d’un atlas initial de 16 384 cellules compactes;
- schémas JSON Draft 2020-12;
- CI matérialisant 10 000 cellules de campagne plus 16 384 cellules seed sans plafond permanent.

## Commandes

```bash
python -m omega_polyglot_bench_t.r02 catalog --count 1024 --output /tmp/catalog.json
python -m omega_polyglot_bench_t.r02 frontier --algorithms 1024
python -m omega_polyglot_bench_t.r02 inspect 1000003 --algorithms 1024
python -m omega_polyglot_bench_t.r02 materialize --algorithms 1024 --count 10000 --output-dir /tmp/campaign
python -m omega_polyglot_bench_t.r02 generate-affine --language rust --output-dir /tmp/generated
python -m omega_polyglot_bench_t.r02 seed --output-dir /tmp/seed
python -m omega_polyglot_bench_t.r02 hardware
```

Après installation du projet :

```bash
omega-polyglot-r02 frontier --algorithms 1024
```

## États épistémiques

Une cellule suit explicitement :

```text
LOGICAL → GENERATED → COMPILED → TESTED → BENCHMARKED → CERTIFIED → SELECTED
                    ↘ REJECTED → ARCHIVED
```

La présence dans l’atlas ne vaut pas preuve de correction. La génération de source ne vaut pas compilation. La compilation ne vaut pas équivalence numérique. Un benchmark ne vaut pas domination universelle.

## Absence de maximum fixe

Aucune constante `MAX_VARIANTS` ne limite la frontière totale. Une campagne possède un budget local explicite, un intervalle, des checkpoints et une capacité de reprise. La limite est donc opératoire et révisable, non présentée comme une frontière théorique permanente.

## OAK

R0.2 n’affirme pas :

- que 2,68 milliards de variantes ont été exécutées;
- que les 1 024 spécifications sont toutes des implémentations complètes;
- qu’un backend gagne sur tout matériel;
- que l’énergie est mesurée;
- qu’un kernel généré hors du sous-ensemble affine est certifié;
- que la taille du dépôt constitue une preuve de progrès scientifique.

Le gain réel est l’adressabilité déterministe, la génération reproductible, la mémoire des échecs et la capacité de matérialiser progressivement la frontière selon la valeur d’information.
