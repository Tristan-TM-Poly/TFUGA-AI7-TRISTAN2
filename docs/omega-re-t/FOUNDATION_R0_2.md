# Ω-RE-T∞ R0.2 — Foundation Expansion

## Statut

R0.2 étend le laboratoire R0.1 vers une infrastructure de reconstruction active, probabiliste, temporelle, traçable et explicitement autorisée. Tous les cas livrés dans RE-16 et RE-256 sont synthétiques. Aucun résultat ne porte sur un système tiers réel.

## 1. Invariants d’autorisation

Toute campagne doit déclarer un `AuthorizationContract` avant l’exécution. Le contrat contient l’objet analysé, l’autorité, le but, les actions autorisées et refusées, les classes de données, les budgets, la rétention, le besoin clean-room et les conditions d’arrêt.

Le moteur est fail-closed : une action non déclarée est refusée. Les actions sensibles restent soumises à révision explicite, même lorsqu’elles apparaissent dans une liste d’actions permises.

## 2. RE-IR

RE-IR représente les entités, composants, ports, états, variables, observations, hypothèses, expériences, contraintes, claims, résidus, versions, permissions et artefacts dans un graphe dirigé et hypergraphique.

Chaque nœud possède un niveau épistémique : observé, mesuré, dérivé, inféré, plausible, reconstruit, causalement supporté, indépendamment répliqué, vérifié dans un domaine, falsifié ou inconnu.

Les graphes fournissent :

- validation des provenances;
- chemins de dépendance;
- composantes fortement connexes;
- sous-graphes induits;
- fusion avec politique de conflit;
- sérialisation canonique;
- digest SHA-256;
- couverture de provenance.

## 3. Automates probabilistes

`ProbabilisticMealyMachine` modélise les sorties et transitions stochastiques. Le moteur calcule la distribution complète des séquences, la vraisemblance, le posterior, l’entropie, la prédiction de mélange, la distance de variation totale et le gain d’information attendu.

La stochasticité n’est pas automatiquement assimilée à une erreur de mesure. Les deux hypothèses doivent rester séparées.

## 4. Automates temporels

`TimedMealyMachine` associe à chaque transition une sortie et un modèle de latence borné. Deux systèmes ayant les mêmes sorties peuvent être distingués par leur dynamique temporelle. Les observations conservent explicitement entrées, sorties et latences.

## 5. Tomographie de contraintes

`ConstraintSet` intersecte des contraintes d’égalité, d’inégalité, d’appartenance, d’absence, de conservation, de temporalité, de capacité ou de topologie.

Les non-observations sont conservées par `NegativeSpaceRecord`. Une absence répétée devient une contrainte pondérée, jamais une impossibilité absolue sans domaine et confiance déclarés.

## 6. Residual Miner

Les résidus sont classés en bruit, biais, dérive, périodicité, dépendance d’état, mélange de versions, effet instrument, variable manquante, échec de classe de modèle ou inconnu.

L’Unknown-Unknown Radar signale les résidus structurés qu’aucune famille actuelle n’explique suffisamment. Le système doit pouvoir conclure que son atlas de mécanismes est incomplet.

## 7. Stockage probatoire

R0.2 ajoute :

- JSONL canonique avec hash par enregistrement;
- SQLite avec clés étrangères;
- campagnes;
- observations;
- hypothèses révisées;
- artefacts;
- checkpoints chaînés;
- transactions et rollback;
- vérification d’intégrité de campagne.

La chaîne de checkpoints permet une reprise déterministe et révèle les ruptures de provenance.

## 8. RE-16

RE-16 couvre seize problèmes synthétiques :

1. machine de Mealy;
2. état inaccessible;
3. sorties probabilistes;
4. distinction par latence;
5. format fixe;
6. versions et champs optionnels;
7. handshake;
8. retry et timeout;
9. oscillateur amorti;
10. système thermique;
11. thermostat hybride;
12. processus avec boucle;
13. généalogie de régression;
14. cartographie comportementale IA;
15. classe de modèle inconnue;
16. spécification clean-room.

Chaque cas contient vérité synthétique, observations, modèles candidats, budget, résultat attendu, contrôles négatifs, modes d’échec, tags, autorisation et digest.

## 9. RE-256

RE-256 applique seize perturbations à chacun des seize cas RE-16 : baseline, permutation de labels, perte et duplication de données, bruit léger et modéré, budgets serré et large, prior biaisé, mélange de versions, provenance manquante, offset instrumental, jitter temporel, contrôle négatif, région non observée et classe vraie absente.

Le manifeste distingue obligatoirement :

```text
cas logiquement définis
cas matérialisés
cas exécutés
cas ayant passé un test logiciel
cas validés scientifiquement
```

La matérialisation de 256 cas ne constitue ni 256 expériences exécutées ni 256 validations scientifiques.

## 10. Exécution

```bash
python -m pytest -q tests/test_omega_re_*.py
python -m omega_re_t.r02_cli catalog
python -m omega_re_t.r02_cli frontier --materialize benchmarks/omega-re/re256.json
python -m omega_re_t.r02_cli demo-prob
python -m omega_re_t.r02_cli demo-timed
python -m omega_re_t.r02_cli db-demo
```

Après installation :

```bash
omega-re-r02 catalog
omega-re-r02 frontier --materialize benchmarks/omega-re/re256.json
omega-re-r02 demo-prob
omega-re-r02 demo-timed
omega-re-r02 db-demo
```

## 11. Frontière suivante

R0.3 doit ajouter :

- apprentissage actif d’automates sans énumération exhaustive;
- automates partiels et non déterministes;
- causal graph interventionnel;
- grammaires de formats synthétiques;
- protocoles jouets générés;
- systèmes hybrides continus;
- version genealogy;
- spécification clean-room multi-agent;
- RE-32 puis RE-64;
- campagnes shardées avec reprise et Merkle receipts.

## 12. Doctrine OAK

Une haute fidélité comportementale n’implique pas l’identité interne. Une absence observée n’est pas une impossibilité universelle. Un meilleur modèle parmi de mauvais modèles n’est pas une explication suffisante. Une reconstruction reste bornée par son contrat, ses données, son domaine et sa dette d’identifiabilité.
