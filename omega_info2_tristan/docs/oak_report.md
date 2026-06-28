# OAK Report — Ω-INFO²-T MVP+

## Statut

MVP logiciel enrichi poussé sur branche `feat/omega-info2-tristan` et attaché à la PR #139.

## Ce qui est implémenté

- Modèles typés : `InfoObject`, `Claim`, `MetaInformation`, `Provenance`, `UncertaintyTensor`, `InfoScores`, `OAKReport`, `InfoAction`.
- Statuts OAK : `RAW`, `PARSED`, `COMPRESSED`, `LINKED`, `TESTABLE`, `TESTED`, `FALSIFIED`, `ROBUST`, `CANONICAL`, `DANGEROUS`, `IP-SENSITIVE`.
- Routes d’action : `PROTOTYPE`, `PATENT_HOLD`, `M_MINUS`, `OAK_REVIEW`, `CANON_CANDIDATE`, etc.
- `BayesTristanUpdater` : posterior vectoriel vérité/utilité/fertilité/testabilité/sûreté/rentabilité/nouveauté.
- `CVCDCompressor` : extraction MVP d’invariants, compression gain, et résidus.
- `MMinusRegistry` : mémoire négative JSONL/append-only issue des échecs OAK.
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
- GitHub Action CI dédiée `Ω-INFO²-T Tests`.

## Ce qui n’est pas encore prouvé

- Les scores ne sont pas encore calibrés empiriquement.
- L’extraction de claims n’est qu’une heuristique MVP.
- Le graphe n’est pas encore branché à une base réelle.
- Bayes-Tristan utilise des likelihood ratios fournis ou estimés, pas encore appris automatiquement.
- CVCD extrait des invariants lexicaux/conceptuels simples, pas encore des invariants mathématiques profonds.
- M⁻ est persistant en JSONL, mais pas encore relié à une base vectorielle/hypergraphique.

## Résidus conservés

- Besoin d’un benchmark sur corpus réel : papier scientifique, brevet, mesure calibrée, page web récente, email, code.
- Besoin d’une intégration avec Rosette-Tristan pour PDF → Info²Graph.
- Besoin d’une intégration avec GitHub Issues pour convertir les routes en tâches.
- Besoin d’une calibration empirique des poids Bayes/CVCD/OAK.
- Besoin d’une politique IP plus formelle pour `PATENT_HOLD`.

## Prochaines actions recommandées

1. Ajouter un pipeline end-to-end `pipeline.py` : text/PDF stub → InfoObject → Bayes → CVCD → OAK → Router → M⁻ → Graph.
2. Ajouter `rosette_adapter.py` pour brancher les extractions PDF.
3. Ajouter `github_issue_exporter.py` pour transformer les routes en issues.
4. Ajouter benchmarks sur corpus réel.
5. Ajouter une base locale JSONL pour Info2Graph + M⁻.

## OAK conclusion

Ce MVP+ est un **prototype structurant testable**, non une preuve finale. Il respecte la séparation entre information, méta-information, preuve, incertitude, fertilité, risque, compression, posterior bayésien, mémoire négative et action.
