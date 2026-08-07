# Exemple récursif OAKGate jusqu’à la profondeur observée n=9

Cet exemple est généré par `build_oakgate_depth9()`.

```text
OAKGate                                                  n=0
└── OAK-Code                                             n=1
    └── TestInspector                                    n=2
        └── CoverageAnalyzer                             n=3
            └── BranchCoverage                           n=4
                └── MissingBranchDetector                n=5
                    └── compare_expected_to_observed()   n=6
                        └── test_one_branch_missing       n=7
                            └── then_provenance           n=8
                                └── residuals             n=9
```

Une seconde branche développe :

```text
OAK-Documentation → ClaimCodeConsistency → ClaimExtractor
→ MarkdownClaimExtractor → SentenceClassifier → classify_claim()
```

## Sorties générées

- `depth-graph.json` : graphe complet;
- `nodes.jsonl` : flux d’un nœud par ligne;
- `tree.md` : navigation humaine;
- `depth-graph.graphml` : import dans un outil de graphes;
- `oak-report.json` : résumé, statuts et problèmes de validation.

`n=9` est la profondeur observée de cet exemple fini. Ce n’est ni la profondeur maximale d’OAKGate, ni une limite globale de l’architecture.
