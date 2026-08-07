# Ω-SUMMARY-FRACTAL-T∞

## Statut

Logiciel de recherche, documentation et audit structurel. Il ne transforme pas la présence d'un README, de code ou de tests en preuve scientifique, nouveauté, sécurité, brevetabilité, traction commerciale ou vérité causale.

## Phrase-mère

> Tout artefact doit pouvoir être compressé vers un résumé parent et tout résumé important doit pouvoir être audité en redescendant vers les artefacts qui l'ont produit.

## Objet

Le système définit `S(object, depth, audience, time, focus)` avec objet, profondeur D0-D9, audience, version observée et sous-graphe de focus.

## Profondeurs

| Niveau | Vue |
|---:|---|
| D0 | dépôt seulement |
| D1 | systèmes détectés |
| D2 | + documents |
| D3 | + workflows et schémas + lacunes |
| D4 | + code/tests + déduplication heuristique |
| D5 | + données et artefacts |
| D6 | + classes/fonctions Python |
| D7 | vue complète locale |
| D8 | vue complète + audit OAK |
| D9 | vue complète destinée à la reconstruction/navigation |

`D∞` est une opération interactive de zoom, pas un fichier infiniment long.

## Invariants

1. Evidence first — les nœuds fichier portent un SHA-256.
2. Status separation — `documented`, `implemented`, `tested` restent distincts.
3. No validation laundering — des tests logiciels ne deviennent jamais automatiquement une validation scientifique.
4. Deterministic replay — `SOURCE_DATE_EPOCH` permet des sorties reproductibles en CI.
5. Compression ascendante / audit descendant — les résumés gardent les chemins vers les sources.
6. Review for semantic claims — doublons/interprétations restent des candidats à revue.
7. Bounded scanning — nombre de fichiers et taille de texte sont bornés.

## Sorties

`.omega/summary/` reçoit `SUMMARY.md`, `STATUS.md`, `OAK_REPORT.md`, `NEXT_ACTIONS.md`, `SUMMARY_INDEX.json`, `depth_index.json` et `summary_d0..d9_<audience>.{md,json}`.

## Intégrations prévues

Ω-GITHUB-BRAIN-T, INFO², OAKGate, Rosette, Asset Factory, M⁻ et Ω-BIAS-OAK-T.

## Non-claims

La v0.1 ne prétend pas comprendre sémantiquement tout le corpus, résoudre les synonymes entre dépôts, certifier des revendications scientifiques, déterminer automatiquement la nouveauté IP, mesurer la valeur commerciale ou remplacer un reviewer humain. Elle fournit le substrat déterministe et testable sur lequel ces couches peuvent être ajoutées.
