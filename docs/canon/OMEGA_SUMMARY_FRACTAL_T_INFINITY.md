# Ω-SUMMARY-FRACTAL-T∞

## Statut

Logiciel de recherche, documentation et audit structurel. Il ne transforme pas la présence d'un README, de code, de tests, de CI, de schémas, d'objets générés, d'un grand espace logique, d'un cluster de systèmes ou d'une hausse de métriques Git en preuve scientifique, nouveauté, sécurité, brevetabilité, traction commerciale ou vérité causale.

## Phrase-mère

> Tout artefact doit pouvoir être compressé vers un résumé parent, tout résumé important doit pouvoir être audité en redescendant vers les artefacts qui l'ont produit, et toute évolution importante doit pouvoir être comparée à un état antérieur sans inventer de progrès non observé.

## Objet

Le système définit :

`S(object, depth, audience, time, focus)`

avec objet, profondeur D0-D9, audience, version observée et sous-graphe de focus.

R0.2 ajoute :

`L(system) = {first_seen, chronology_rank, status, evidence_relations}`

et :

`ΔS = S(t1) - S(t0)`

R0.3 ajoute un index longitudinal chaîné :

`I_n = H(I_{n-1}, S_n)`

et une projection de cristallisation structurelle :

`C_struct = (docs + code + tests + CI + schema) / 5`

ainsi qu'une dette structurelle `D_struct` comptant les éléments manquants observables. Ces métriques sont des instruments de pilotage logiciel, jamais des métriques de vérité scientifique.

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
| D9 | vue complète destinée à reconstruction/navigation/historique |

`D∞` est une opération interactive de zoom, pas un fichier infiniment long.

## Relations structurales

Le graphe peut porter notamment :

- `CONTAINS` — containment de dépôt;
- `DECLARES` — symbole déclaré par un fichier;
- `TESTS` — test rattaché à un système;
- `VALIDATES` — workflow CI rattaché à un système;
- `CONFORMS_TO` — contrat/schéma rattaché à un système;
- `SUPPORTS` — document de support rattaché à un système;
- `DEPENDS_ON` — dépendance Python inter-systèmes observée.

Les extensions `IMPLEMENTS`, `BENCHMARKS`, `CONTRADICTS`, `SUPERSEDES` et `GENERATED_FROM` restent réservées aux couches où une provenance explicite suffisante est disponible; elles ne doivent pas être inventées par simple similarité lexicale.

## Chronologie

`first_seen` provient de l'historique Git disponible. Si l'historique est absent, shallow ou réécrit, le système conserve une valeur manquante et `chronology_source=unavailable` plutôt que d'inventer une date.

La chronologie Git n'est pas une preuve de date d'invention, de priorité scientifique ou de priorité IP.

## R0.3 — CorpusIndex persistant

Chaque snapshot peut être ajouté à un index logiquement append-only :

- chaque entrée porte `previous_hash`;
- chaque entrée possède `entry_hash = SHA256(previous_hash || snapshot canonique)`;
- un fingerprint déjà présent n'est pas ajouté deux fois;
- l'intégrité de la chaîne est vérifiable;
- l'index accepte un résumé de dépôt ou un résumé multi-dépôts.

Le mode `omega-summary-corpus` alimente automatiquement `CORPUS_INDEX.json` dans son répertoire de sortie. Le mode `all-depths` alimente automatiquement `SUMMARY_HISTORY.json` à D9.

## Longitudinal

`LONGITUDINAL_CRYSTALLIZATION.{json,md}` mesure par système :

- premier/dernier run observé;
- nombre de runs où le système est visible;
- transitions de statut;
- cristallisation structurelle initiale/finale;
- delta de cristallisation;
- vitesse par run observé;
- dette structurelle initiale/finale;
- delta de dette.

La vitesse est volontairement exprimée par **run observé**, pas comme une vitesse scientifique ou une productivité humaine.

## Convergence multi-preuves

R0.3 distingue :

1. paires `shared-kernel-candidate`;
2. clusters `multi-evidence-superkernel-candidate`.

Les canaux peuvent inclure :

- similarité lexicale;
- dépendance directe;
- dépendances partagées;
- chevauchement du profil de validation.

Un super-kernel exige plusieurs canaux structurels. Dans tous les cas :

- `status=review_required`;
- `automatic_merge=false`;
- aucune suppression automatique;
- aucune conclusion d'identité, redondance, nouveauté ou propriété.

## Exports graphe

R0.3 produit :

- `SUMMARY_GRAPH.jsonl` — nœuds et arêtes streamables;
- `SUMMARY_GRAPH.graphml` — projection GraphML sans dépendance externe;
- `SUMMARY_GRAPH_EXPORT.json` — manifeste de fingerprint et cardinalités.

Ces exports permettent de brancher graph DB, notebooks, visualisation, INFO², OAKGate, GitHub Brain et moteurs de requêtes sans rendre le format Markdown canonique.

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
10. Delta is structural — `ΔSummary` mesure les changements du dépôt, pas une hausse automatique de vérité, valeur ou originalité.
11. History is integrity-bound — l'index longitudinal est hash-chaîné et dédupliqué par fingerprint.
12. Crystallization is structural — `C_struct` mesure docs/code/tests/CI/schémas, pas la vérité du contenu.
13. Clustering is advisory — aucun cluster n'autorise une fusion ou suppression automatique.

## Sorties D9

`.omega/summary/` peut recevoir :

- `SUMMARY.md`;
- `STATUS.md`;
- `OAK_REPORT.md`;
- `NEXT_ACTIONS.md`;
- `EVOLUTION.md`;
- `PROOF_DEBT.md`;
- `CONVERGENCE_CANDIDATES.md`;
- `SYSTEM_LINEAGE.json`;
- `SUMMARY_INDEX.json`;
- `SUMMARY_HISTORY.json`;
- `depth_index.json`;
- `summary_d0..d9_<audience>.{md,json}`;
- `longitudinal/LONGITUDINAL_CRYSTALLIZATION.{json,md}`;
- `graph/SUMMARY_GRAPH.{jsonl,graphml}`;
- `graph/SUMMARY_GRAPH_EXPORT.json`.

L'opérateur :

`omega-summary delta previous.json current.json`

produit :

- `DELTA_SUMMARY.json`;
- `DELTA_SUMMARY.md`.

Le mode corpus produit aussi :

- `CORPUS_SUMMARY.{json,md}`;
- `CORPUS_INDEX.json`;
- `longitudinal/`;
- les vues par dépôt si elles ne sont pas désactivées.

## CLI R0.3

```bash
omega-summary all-depths . --audience oak --output-dir .omega/summary
omega-summary delta previous.json current.json --output-dir .omega/delta
omega-summary index summary_d9_oak.json --index-file .omega/corpus-index.json --report-dir .omega/longitudinal
omega-summary export summary_d9_oak.json --output-dir .omega/graph
omega-summary-corpus --workspace /path/to/repos --depth 9 --audience oak --output-dir .omega/corpus-summary
```

## Dette de preuve

`PROOF_DEBT.md` mesure seulement la dette structurelle observable : documentation, implémentation, tests, contrats et CI liés. La validation externe scientifique, commerciale, juridique ou de sécurité reste explicitement `not_inferred`.

## Intégrations prévues

Ω-GITHUB-BRAIN-T, INFO², OAKGate, Rosette, Asset Factory, M⁻, Ω-BIAS-OAK-T, graph DB et tableaux de bord longitudinaux.

## Non-claims

R0.3 ne prétend pas comprendre sémantiquement tout le corpus, résoudre tous les synonymes entre dépôts, certifier des revendications scientifiques, déterminer automatiquement la nouveauté IP, mesurer la valeur commerciale, reconstruire toute l'histoire scientifique d'une idée, ni remplacer un reviewer humain. Elle fournit un substrat déterministe, chronologique, différentiel, longitudinal, exportable et testable sur lequel ces couches peuvent être ajoutées.
