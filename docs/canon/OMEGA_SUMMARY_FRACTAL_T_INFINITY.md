# Ω-SUMMARY-FRACTAL-T∞

## Statut

Logiciel de recherche, documentation et audit structurel. Il ne transforme pas la présence d'un README, de code, de tests, de CI, de schémas, d'objets générés ou d'un grand espace logique en preuve scientifique, nouveauté, sécurité, brevetabilité, traction commerciale ou vérité causale.

## Phrase-mère

> Tout artefact doit pouvoir être compressé vers un résumé parent, tout résumé important doit pouvoir être audité en redescendant vers les artefacts qui l'ont produit, et toute évolution importante doit pouvoir être comparée à un état antérieur sans inventer de progrès non observé.

## Objet

Le système définit `S(object, depth, audience, time, focus)` avec objet, profondeur D0-D9, audience, version observée et sous-graphe de focus.

R0.2 ajoute une couche temporelle et relationnelle :

`L(system) = {first_seen, chronology_rank, status, evidence_relations}`

et un opérateur de différence :

`ΔS = S(t1) - S(t0)`

qui mesure seulement des changements de dépôt observables.

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

## Relations structurales R0.2

Le graphe peut porter notamment :

- `CONTAINS` — containment de dépôt;
- `DECLARES` — symbole déclaré par un fichier;
- `TESTS` — test racine rattaché à un système;
- `VALIDATES` — workflow CI rattaché à un système;
- `CONFORMS_TO` — contrat/schéma rattaché à un système;
- `SUPPORTS` — document de support rattaché à un système;
- `DEPENDS_ON` — dépendance Python inter-systèmes observée.

Ces relations sont des observations/reconstructions structurelles. Elles ne prouvent pas causalité scientifique, identité sémantique, nouveauté ou propriété.

## Chronologie

`first_seen` provient de l'historique Git disponible. Si l'historique est absent, shallow ou réécrit, le système conserve une valeur manquante et `chronology_source=unavailable` plutôt que d'inventer une date.

La chronologie Git n'est pas une preuve de date d'invention, de priorité scientifique ou de priorité IP.

## Invariants

1. Evidence first — les nœuds fichier portent un SHA-256.
2. Status separation — `observed`, `documented`, `implemented`, `tested` restent distincts.
3. No validation laundering — tests/CI ne deviennent jamais automatiquement une validation scientifique.
4. Deterministic replay — `SOURCE_DATE_EPOCH` permet des sorties reproductibles en CI.
5. Compression ascendante / audit descendant — les résumés gardent les chemins vers les sources.
6. Review for semantic claims — doublons, convergence et interprétations restent des candidats à revue.
7. Bounded scanning — nombre de fichiers et taille de texte sont bornés.
8. Chronology without invention — date Git absente = date absente.
9. Generated volume is not discovery — quantité d'objets/lignes/espace logique n'est pas une preuve de progrès scientifique.
10. Delta is structural — `ΔSummary` mesure les changements du dépôt, pas une hausse automatique de vérité, de valeur ou d'originalité.

## Sorties

`.omega/summary/` reçoit :

- `SUMMARY.md`;
- `STATUS.md`;
- `OAK_REPORT.md`;
- `NEXT_ACTIONS.md`;
- `EVOLUTION.md`;
- `PROOF_DEBT.md`;
- `CONVERGENCE_CANDIDATES.md`;
- `SYSTEM_LINEAGE.json`;
- `SUMMARY_INDEX.json`;
- `depth_index.json`;
- `summary_d0..d9_<audience>.{md,json}`.

L'opérateur `omega-summary delta previous.json current.json` produit :

- `DELTA_SUMMARY.json`;
- `DELTA_SUMMARY.md`.

## Dette de preuve

`PROOF_DEBT.md` mesure seulement la dette structurelle observable : documentation, implémentation, tests, contrats et CI liés. La validation externe scientifique, commerciale, juridique ou de sécurité reste explicitement `not_inferred`.

## Convergence

`CONVERGENCE_CANDIDATES.md` propose des paires `shared-kernel-candidate` à partir de preuves structurelles faibles (similarité lexicale et dépendances observées). Le statut est toujours `review_required`; `automatic_merge=false` est invariant.

## Intégrations prévues

Ω-GITHUB-BRAIN-T, INFO², OAKGate, Rosette, Asset Factory, M⁻ et Ω-BIAS-OAK-T.

## Non-claims

R0.2 ne prétend pas comprendre sémantiquement tout le corpus, résoudre les synonymes entre dépôts, certifier des revendications scientifiques, déterminer automatiquement la nouveauté IP, mesurer la valeur commerciale, reconstruire toute l'histoire scientifique d'une idée, ni remplacer un reviewer humain. Elle fournit un substrat déterministe, chronologique, différentiel et testable sur lequel ces couches peuvent être ajoutées.
