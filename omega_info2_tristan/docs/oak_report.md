# OAK Report — Ω-INFO²-T MVP

## Statut

MVP logiciel initial poussé sur branche `feat/omega-info2-tristan`.

## Ce qui est implémenté

- Modèles typés : `InfoObject`, `Claim`, `MetaInformation`, `Provenance`, `UncertaintyTensor`, `InfoScores`, `OAKReport`, `InfoAction`.
- Statuts OAK : `RAW`, `PARSED`, `COMPRESSED`, `LINKED`, `TESTABLE`, `TESTED`, `FALSIFIED`, `ROBUST`, `CANONICAL`, `DANGEROUS`, `IP-SENSITIVE`.
- Routes d’action : `PROTOTYPE`, `PATENT_HOLD`, `M_MINUS`, `OAK_REVIEW`, `CANON_CANDIDATE`, etc.
- SourceTrustKernel.
- InfoHalfLife estimator.
- OAKInfoGate.
- InfoRouter.
- Info2Graph.
- Extracteur déterministe de claims candidats.
- CLI JSON.
- Schéma YAML.
- Exemples paper/patent/calibration.
- Tests unitaires.

## Ce qui n’est pas encore prouvé

- Les scores ne sont pas encore calibrés empiriquement.
- L’extraction de claims n’est qu’une heuristique MVP.
- Le graphe n’est pas encore branché à une base réelle.
- Le moteur Bayes-Tristan vectoriel n’est pas encore implémenté.
- La compression CVCD est représentée par des champs et scores, pas encore par un algorithme complet.

## Résidus conservés

- Besoin d’un benchmark sur corpus réel : papier scientifique, brevet, mesure calibrée, page web récente, email, code.
- Besoin d’une mémoire M⁻ pour les erreurs de sources et hallucinations.
- Besoin d’une intégration avec Rosette-Tristan pour PDF → Info²Graph.
- Besoin d’une intégration avec GitHub Issues pour convertir les routes en tâches.

## Prochaines actions recommandées

1. Ajouter `bayes_tristan.py` pour posterior vectoriel vérité/utilité/fertilité/testabilité/sûreté/rentabilité/nouveauté.
2. Ajouter `cvcd_compressor.py` pour extraction d’invariants et résidus.
3. Ajouter `m_minus_registry.py` persistant.
4. Ajouter un connecteur Rosette-Tristan.
5. Ajouter tests de bout en bout sur exemples réels.

## OAK conclusion

Ce MVP est un **prototype structurant testable**, non une preuve finale. Il respecte la séparation entre information, méta-information, preuve, incertitude, fertilité, risque et action.
