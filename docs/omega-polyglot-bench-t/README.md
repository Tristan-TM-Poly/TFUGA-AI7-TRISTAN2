# Ω-POLYGLOT-BENCH-T R0.1

Laboratoire OAK-safe pour conserver plusieurs implémentations d'un même algorithme en Python, C, C++ et Rust, vérifier leur équivalence, comparer leurs performances et sélectionner un backend sans supprimer les autres.

## Statut

Ce module est un prototype de logiciel de recherche. Un résultat de benchmark dépend du matériel, du compilateur, des options, du système, de la taille des données, du coût FFI et du scénario d'appel. Il ne prouve pas qu'un langage est universellement supérieur.

## Architecture

```text
spécification comportementale
        |
        +-- Python : oracle lisible et orchestration
        +-- C      : ABI minimale et noyau portable
        +-- C++    : noyau scientifique/HPC
        +-- Rust   : noyau natif sûr et concurrent
        |
        +-- même jeu de données déterministe
        +-- conformité numérique
        +-- mesures froides et chaudes
        +-- sélection parmi les backends conformes
```

Le premier kernel est `vector_affine_f64` :

```text
output[i] = scalar * x[i] + y[i]
```

Il valide la chaîne complète avant d'introduire des kernels plus complexes comme FFWT, déconvolution lorentzienne, tenseurs, graphes, fluides ou cristaux.

## Commandes

Compiler les bibliothèques natives :

```bash
python -m omega_polyglot_bench_t build
```

Comparer Python, C, C++ et Rust :

```bash
python -m omega_polyglot_bench_t compare --size 100000 --repetitions 15
```

Construire puis comparer en une commande :

```bash
python -m omega_polyglot_bench_t compare --build-native --output report.json
```

Limiter la comparaison :

```bash
python -m omega_polyglot_bench_t compare --backends python,rust --size 1000000
```

Après l'intégration du script `pyproject.toml`, les mêmes opérations sont disponibles avec `omega-polyglot`.

## Rapport

Le JSON contient notamment :

- disponibilité de chaque backend;
- conformité à l'oracle Python;
- erreur absolue maximale;
- latence du premier appel;
- médiane, moyenne et p95 des appels mesurés;
- nombre de répétitions;
- backend sélectionné;
- déclaration explicite que les conversions FFI et la matérialisation de sortie sont incluses.

Le sélecteur ne considère jamais un backend indisponible ou incorrect, même s'il semble plus rapide.

## Protocole pour ajouter un algorithme

1. Définir les entrées, sorties, types, unités, erreurs et tolérances.
2. Écrire une version Python claire servant d'oracle comportemental.
3. Définir une ABI C stable pour le kernel.
4. Implémenter C, C++ et Rust derrière exactement la même ABI.
5. Générer des vecteurs normaux, limites, aléatoires et adversariaux.
6. Vérifier l'équivalence avant toute mesure de vitesse.
7. Mesurer petits et grands régimes, appels froids et chauds, mémoire et conversions.
8. Conserver les résultats par matériel, compilateur et commit.
9. Marquer chaque backend par rôle : référence, petite taille, grande taille, mémoire faible, service sûr ou embarqué.
10. Ne promouvoir un backend par défaut qu'après reproductibilité CI et benchmark sur le matériel cible.

## OAK : faux gains interdits

- comparer des algorithmes mathématiquement différents;
- exclure les conversions d'un backend mais pas d'un autre;
- comparer appel froid contre appel chaud;
- accepter une erreur numérique supérieure à la tolérance;
- généraliser un résultat obtenu sur une seule taille ou une seule machine;
- confondre performance d'une bibliothèque et performance intrinsèque d'un langage;
- supprimer les backends perdants alors qu'ils peuvent gagner dans un autre régime;
- présenter un benchmark CI virtualisé comme mesure énergétique ou industrielle.

## Limites R0.1

- un seul kernel de validation;
- calcul CPU `float64` seulement;
- Linux et macOS pour la compilation automatique;
- métriques temporelles seulement, sans RSS, énergie, SIMD détecté ou perf counters;
- conversion Python/ctypes incluse et non encore séparée du temps du kernel;
- sélection locale par médiane, sans base historique par profil matériel.

## Prochaines extensions

- séparation `kernel-only`, `conversion-only` et `end-to-end`;
- profils matériel/OS/compilateur versionnés;
- mémoire maximale, débit, énergie et taille binaire;
- NumPy/Numba/JAX comme backends Python accélérés distincts;
- SIMD, OpenMP/Rayon et GPU;
- sélecteur multiobjectif latence/mémoire/énergie/précision;
- kernels FFWT, TensorProdLift, convolution/déconvolution et hypergraphe;
- historique M-minus des régressions, erreurs numériques et résultats non reproductibles.
