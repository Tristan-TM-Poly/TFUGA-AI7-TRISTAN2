# OAKBench Manifest

## But

Définir les benchmarks minimaux pour prouver qu'un module Ω-AI-TRISTAN-LAB fonctionne mieux qu'une note de cours ou une réponse non vérifiée.

## Benchmarks initiaux

| Benchmark | Entrée | Sortie attendue | Métrique |
|---|---|---|---|
| idea_to_card | idée brute | TheoryCard complète | champs présents + risques + tests |
| oak_eval | TheoryCard | OAKReport | score borné + next action |
| bayes_score | TheoryCard + evidence | BayesAxisScore | axes séparés + décision |
| ip_gate | TheoryCard | IPClassification | actions sûres/bloquées |
| revenue_map | TheoryCard | RevenuePath[] | validation_test + risques |
| rag_retrieval | corpus court + requête | chunk pertinent | source correcte top-1 |

## Baselines

- Réponse texte sans structure.
- TODO list manuelle.
- Résumé sans tests.
- Agent sans IP gate.
- Agent sans mémoire négative.

## Critère de réussite MVP

Le MVP est acceptable si :

1. `pytest` passe.
2. La CLI retourne un JSON valide.
3. Chaque idée produit risques + tests + prochaine action.
4. Les actifs potentiellement brevetables déclenchent IP_LOCK ou IP review.
5. Aucun module ne promet vérité, autonomie totale ou revenu garanti.
