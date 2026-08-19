# Claim Ledger — La Loi du Minimum Suffisant R0.1

Ce ledger sépare doctrine, hypothèse, définition, résultat mathématique à démontrer et programme expérimental.

| ID | Claim | Status | Falsifier / test minimal |
|---|---|---|---|
| LMS-001 | Toute complexité persistante devrait justifier son existence par une capacité mesurable perdue à l'ablation. | Design doctrine | Trouver une classe de systèmes où une complexité non-ablatable reste rationnellement nécessaire sans valeur optionnelle, sécurité, redondance ou autre capacité mesurable. |
| LMS-002 | La minimalité utile est conditionnée par le but et les invariants, pas absolue. | Definition / design theorem target | Construire deux objectifs différents montrant que le même sous-système est minimal dans l'un et non dans l'autre. |
| LMS-003 | LocalPASS n'implique pas GlobalPASS. | General systems principle | Exhiber et formaliser une composition où tous les modules passent localement mais la composition viole un invariant global. |
| LMS-004 | Une représentation par quotient causal peut réduire un espace d'état sans perte décisionnelle au-delà d'une tolérance explicite. | Hypothesis / known-method family | Mesurer erreur, coût et robustesse contre représentation complète sur cas contrôlés. |
| LMS-005 | Une stratégie Generate→Ablate→Verify peut produire une meilleure densité de capacité vérifiée qu'une stratégie d'accumulation. | Experimental hypothesis | Benchmark multi-domaines contre baseline add-only à budget égal. |
| LMS-006 | Regenerate-on-demand peut réduire coût de maintenance total lorsque le coût de régénération reste inférieur au coût de persistance. | Engineering hypothesis | Mesurer TCO persistance vs régénération, incluant latence, énergie, risque et failure recovery. |
| LMS-007 | Une base génératrice minimale ou quasi-minimale peut compresser un corpus de capacités sans perte de fermeture utile déclarée. | Algorithmic hypothesis | Recherche exacte sur petits univers + approximation sur grands univers, avec comparaison de fermeture. |
| LMS-008 | Le même méta-opérateur peut être instancié à plusieurs échelles si chaque échelle fournit un contrat propre. | Architecture hypothesis | Implémenter trois domaines hétérogènes avec ABI commune et métriques spécifiques ; mesurer réutilisation réelle. |
| LMS-009 | Les séquences d'opérateurs récurrentes peuvent être fusionnées en primitives apprises sans perte d'invariants. | Compiler hypothesis | Macro-instruction vs pipeline original : équivalence, latence, complexité, erreurs. |
| LMS-010 | La simplification peut être rendue réversible par reçus de transformation et stratégie de régénération. | Engineering hypothesis | Round-trip compress→regenerate sur jeux d'essai, mesurer résidu et invariants. |
| LMS-011 | La terminologie « Simplification Quantique de Tristan » ne constitue pas une revendication de phénomène quantique physique. | OAK boundary | Toute extension physique doit introduire modèle quantique explicite, observables, prédictions et validation séparée. |
| LMS-012 | Le livre peut devenir theory-as-code : claims, tests, exemples, contre-exemples et provenance doivent évoluer ensemble. | Project doctrine | CI scientifique détectant au moins claims cassés, liens de preuve manquants et régressions d'exemples. |

## Promotion rule

Aucun claim ne passe à `VERIFIED` par répétition rhétorique. La promotion exige un reçu OAK avec baseline, résultat, méthode, incertitude, provenance et limites.

## Negative memory seeds

- `M-LMS-COMPLEXITY-001`: minimalité sans invariants peut supprimer sécurité, redondance ou option future utile.
- `M-LMS-QSIM-001`: vocabulaire quantique métaphorique ne doit pas être présenté comme nouvelle mécanique quantique.
- `M-LMS-GLOBALPASS-001`: ablation locale peut casser une capacité à une autre échelle.
- `M-LMS-REGEN-001`: régénérer à la demande peut être pire que persister si latence, énergie, dépendances ou indisponibilité dominent.
- `M-LMS-METRIC-001`: une fonction objectif unique mal calibrée peut Goodhartiser le système ; front de Pareto avant scalarisation.
