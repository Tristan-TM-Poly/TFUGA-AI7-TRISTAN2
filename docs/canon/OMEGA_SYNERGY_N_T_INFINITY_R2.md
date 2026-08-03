# Ω-SYNERGY-N-T∞ R2

## Théorie exécutable des interactions irréductibles d'ordre n

**Statut :** logiciel de recherche et d'expérimentation, autorité `review_only`.  
**Non-claims :** aucune preuve scientifique, causalité générale, validation commerciale, autorité de fusion ou publication automatique.

## Principe central

Une coalition de `n` créations n'est pas automatiquement une synergie d'ordre `n`.
La valeur propre de la coalition doit rester après soustraction de toutes les interactions de ses sous-coalitions.

Pour une fonction de valeur contextualisée `V(S | contexte, temps)` :

```text
V(S) = somme_{T subset S} I(T)
I(S) = somme_{T subset S} (-1)^(|S|-|T|) V(T)
```

Le moteur R2 conserve séparément :

- gain brut `V(S)-V(empty)`;
- interaction propre `I(S)`;
- valeur des ordres inférieurs;
- coût d'intégration;
- dette synergique;
- risque résiduel;
- synergie nette;
- incertitude et intervalle;
- nécessité de chaque composant;
- contexte et provenance.

## Échelle N0–N10

| Niveau | Signification |
|---|---|
| N0 | candidat combinatoire |
| N1 | compatibilité typée |
| N2 | fermeture théorique |
| N3 | prototype minimal |
| N4 | gain brut mesuré |
| N5 | interaction propre mesurée |
| N6 | interaction causale sous plan adéquat |
| N7 | robustesse multi-contextes |
| N8 | motif réutilisable |
| N9 | validation externe |
| N10 | capacité canonique maintenue |

Le moteur ne promeut jamais seul une coalition au-delà de l'autorité de revue.

## Noyau mathématique

### Inversion de Möbius

Le module `mobius.py` implémente :

- validation de la fermeture complète du treillis;
- transformée de Möbius exacte;
- reconstruction zêta;
- contraste direct d'une coalition;
- propagation RSS des erreurs indépendantes;
- décomposition des mesures en interactions propres;
- nécessité et pureté d'ordre.

L'indépendance des erreurs est une hypothèse déclarée. Des erreurs corrélées exigent une matrice de covariance externe.

### Plans factoriels

Le module `factorial.py` produit :

- plans factoriels complets `2^n`;
- réplications déterministes;
- demi-fractions par parité;
- groupes d'alias explicites;
- contraste de Möbius en codage 0/1;
- effet orthogonal en codage -1/+1.

Un plan fractionnaire ne peut pas être interprété comme s'il identifiait toutes les interactions.

### Spectre d'ordre

Pour chaque ordre, R2 mesure :

- interactions évaluées et possibles;
- nombre positif et négatif;
- énergie positive et négative;
- densité;
- efficacité nette par coût;
- pureté moyenne;
- distribution normalisée et entropie d'ordre.

Un ordre dominant n'est pas automatiquement l'ordre optimal. La dette, le coût, la fragilité et la demi-vie doivent être considérés.

## Synergy Complex

R2 combine :

- hypergraphe des coalitions observées ou candidates;
- fermeture simpliciale des sous-coalitions nécessaires à la preuve;
- incidence nœud-hyperarête;
- projection en graphe;
- composantes connexes;
- détection des faces probatoires manquantes.

Une hyperarête peut exister comme hypothèse avant que toutes ses faces soient mesurées, mais elle ne peut pas recevoir une interaction exacte sans le treillis nécessaire.

## Recherche bornée

Trois moteurs sont fournis :

1. recherche exhaustive pour petits univers;
2. beam search déterministe;
3. branch-and-bound avec borne optimiste prudente.

Le beam search conserve une fraction d'exploration déterministe afin de ne pas éliminer toutes les synergies pures dont les paires semblent faibles.
Les scores de recherche planifient des expériences; ils ne mesurent pas les interactions.

## Minimalité

R2 calcule :

- nécessité marginale d'un composant;
- composants redondants;
- composants nuisibles;
- noyaux minimaux satisfaisant un seuil.

La règle de cristallisation est : préférer la plus petite coalition capable de produire la transformation validée.

## Synergie informationnelle

Le module `information.py` fournit :

- entropie discrète;
- information mutuelle;
- information mutuelle conditionnelle;
- information d'interaction de McGill;
- fixture XOR.

Dans XOR, chaque source est individuellement non informative sur la cible, tandis que la paire la détermine.
L'information d'interaction signée n'est pas une décomposition PID complète et son signe dépend de la convention.

## Tenseur clairsemé

`SparseInteractionTensor` stocke uniquement les interactions observées ou candidates :

- indexation symétrique par ensembles non ordonnés;
- tranches par ordre;
- interactions positives et négatives;
- classement normal ou absolu;
- estimation de sparsité par rapport à l'espace combinatoire.

Une factorisation tensorielle future devra être ajoutée comme approximation séparée et testée contre les valeurs exactes.

## Bayes-Tristan prudent

Le module `bayes.py` fournit une mise à jour gaussienne conjugée minimale :

- prior normal;
- observation avec erreur connue;
- posterior normal;
- probabilité que l'interaction dépasse un seuil.

Cette sortie n'est ni un Bayes factor, ni une preuve, ni une validation causale.

## Contexte et demi-vie

R2 conserve le contexte de chaque mesure et permet :

- comparaison d'une même coalition entre deux contextes;
- intervalle sur la différence;
- décroissance exponentielle de confiance;
- décision `INCREASED`, `DECREASED` ou `INCONCLUSIVE`.

## Hyper-épistasie des PR

Une constellation de PR contient :

- identifiants;
- chemins;
- capacités et besoins;
- dépendances;
- conflits;
- tests;
- rollback.

R2 construit :

- hyperarête de constellation;
- vagues topologiques;
- détection des cycles;
- contraste d'hyper-épistasie à partir des valeurs des sous-ensembles.

Aucune constellation n'autorise une fusion automatique.

## OAK non compensatoire

Les gates minimales sont :

- interfaces typées;
- pertes déclarées;
- provenance;
- baseline vide ou composant;
- baseline la plus simple;
- métrique;
- falsificateur;
- incertitude;
- rollback;
- budget;
- propriétaire;
- journalisation.

Les systèmes récursifs exigent en plus :

- budget fini;
- stop gate;
- gouverneur récursif.

Une action sensible exige un gate humain explicite.

## Bundle probatoire

Le mode `demo` produit :

```text
measurements.json
interactions.json
spectrum.json
experiment.json
manifest.json
```

Chaque artefact reçoit :

- taille;
- SHA-256;
- racine de Merkle;
- epoch déterministe;
- frontières d'autorité.

L'audit détecte les contenus manquants, altérés ou les frontières d'autorité cassées.
L'intégrité cryptographique ne prouve pas la vérité du contenu.

## Fixtures fondatrices

- `pure_triplet`: paires nulles, interaction ternaire positive;
- `reducible_triplet`: valeur entièrement expliquée par les ordres 1 et 2;
- `anti_order4`: interactions bilatérales positives, interaction propre d'ordre 4 négative;
- `synergy_os_order4`: constellation synthétique Intent × Foundry × Proof × Portfolio.

Ces fixtures vérifient le logiciel seulement. Elles ne démontrent aucune propriété du corpus réel.

## Commandes

```bash
python -m omega_synergy_n_t demo --fixture synergy_os_order4 --output-dir /tmp/syn-n
python -m omega_synergy_n_t decompose --input /tmp/syn-n/measurements.json
python -m omega_synergy_n_t spectrum --input /tmp/syn-n/measurements.json
python -m omega_synergy_n_t experiment A B C D --design full
python -m omega_synergy_n_t search --creation-dna creation_dna.json --max-order 6
python -m omega_synergy_n_t oak --candidate candidate.json
python -m omega_synergy_n_t audit --bundle-dir /tmp/syn-n
```

## Première expérience réelle recommandée

Constellation :

```text
Intent Compiler × Synergy Foundry × Proof OS × Portfolio Governor
```

Le plan complet exige 16 configurations.
Les métriques doivent inclure : couverture des exigences, fermeture des besoins, précision des fichiers, tests pertinents, faux positifs, coût, dette, reproductibilité et qualité de décision.

L'interaction propre d'ordre 4 ne sera acceptée que si :

- les 16 configurations sont comparables;
- le contexte est stable;
- les sous-ensembles sont mesurés;
- la baseline la plus simple est battue;
- l'intervalle exclut le seuil choisi;
- les limites et résidus sont conservés.

## Commande canonique

```text
GO COMBINE
→ GO DÉCOMPOSE
→ GO ABLATE
→ GO MESURE
→ GO OAK
→ GO MINIMISE
→ GO MÉTA
```
