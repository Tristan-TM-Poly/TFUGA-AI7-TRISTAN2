# Ω-POLYGLOT-AUTOTUNE-T R0.4

R0.4 transforme le laboratoire Python/C/C++/Rust en sélecteur contextuel mesuré. Il ne cherche pas un langage gagnant universel. Il mesure des candidats pour chaque algorithme, taille, profil de compilation et frontière mémoire, puis conserve un champion par contexte.

## Candidats

- Python pur comme oracle comportemental;
- Python + NumPy avec vues d'entrée zéro copie et sorties préallouées;
- C et C++ `portable`, `native` et `openmp`;
- Rust avec la même ABI, mesuré par CI lorsque Cargo est disponible;
- variantes `scalar`, `unrolled4`, `avx2`, `parallel`;
- chaînes affines fusionnées en un passage ou décomposées en deux passages;
- réductions `sum` et `dot` scalar/AVX2/OpenMP;
- exécution affine in-place.

## Frontières mesurées

R0.4 chronomètre les appels préparés : les buffers sont contigus, leurs pointeurs sont conservés, et aucune liste Python n'est reconstruite dans la région chronométrée. Le coût de préparation est enregistré séparément.

Le débit effectif est un modèle logiciel de trafic minimal, pas un compteur matériel. Les données sont réutilisées entre répétitions et peuvent donc être chaudes dans les caches.

## Résultats locaux robustes

Environnement de référence : Linux x86-64, Python 3.13.5, GCC/G++ 14.2, NumPy 2.3.5, cinq threads OpenMP, trois essais indépendants, sept répétitions par essai.

| Algorithme | Taille | Champion robuste | Médiane des médianes | Gain vs boucle Python |
|---|---:|---|---:|---:|
| affine | 4 096 | C++ portable unrolled4 | 1,873 µs | 90,68× |
| affine | 100 000 | C++ OpenMP parallel | 8,453 µs | 529,11× |
| affine | 1 000 000 | C OpenMP parallel | 76,023 µs | 666,58× |
| chaîne affine | 4 096 | C++ native AVX2 fusionné | 2,444 µs | 93,42× |
| chaîne affine | 100 000 | C++ OpenMP fusionné | 16,024 µs | 353,31× |
| chaîne affine | 1 000 000 | C++ OpenMP fusionné | 96,543 µs | 674,35× |
| somme | 1 000 000 | Python + NumPy | 161,610 µs | 40,29× |
| produit scalaire | 1 000 000 | Python + NumPy | 71,626 µs | 643,99× |

Le meilleur langage change donc avec l'opération et la taille. NumPy reste un candidat Python de première classe plutôt qu'un oracle volontairement lent.

## Gain de fusion mesuré sur une campagne

| Taille | Un passage fusionné vs deux passages natifs |
|---:|---:|
| 4 096 | 1,69× |
| 100 000 | 3,00× |
| 1 000 000 | 2,02× |

La fusion réduit les lectures/écritures intermédiaires et les appels FFI. Elle peut apporter davantage que le passage de C à C++ ou inversement.

## Commandes

```bash
omega-polyglot-r04 build \
  --backends c,cpp,rust \
  --profiles portable,native,openmp

omega-polyglot-r04 autotune \
  --backends c,cpp,rust \
  --profiles portable,native,openmp \
  --algorithms affine,affine_chain,sum,dot \
  --sizes 16,256,4096,100000,1000000 \
  --warmups 3 \
  --repetitions 15 \
  --output report.json

omega-polyglot-r04 robust \
  --trials 5 \
  --sizes 4096,100000,1000000 \
  --output robust.json
```

## Sélection runtime

`AutotunedDispatcher` lit un rapport et choisit le champion de la taille mesurée la plus proche. La décision retournée inclut algorithme, taille demandée, taille d'entraînement, candidat et justification. Un profil ne doit pas être transféré silencieusement vers un matériel différent.

## Verrous OAK

- conformité avant performance;
- tolérance numérique explicite;
- aucun gagnant universel;
- Python/NumPy conservé dans la compétition;
- profils portable, native et OpenMP séparés;
- installation et calcul séparés;
- médiane, p95 et MAD;
- rapports versionnés et artefacts CI;
- Rust non revendiqué localement tant qu'il n'est pas mesuré;
- aucune promesse de gain pour FFWT, graphes, tenseurs ou solveurs avant portage et benchmark propres.
