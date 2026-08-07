# Ω-SUMMARY-FRACTAL-T∞ — Cross-repository corpus layer

## Objectif

Compiler plusieurs checkouts Git en une vue de corpus sans supposer qu'une frontière GitHub correspond à une frontière conceptuelle Ω.

```text
repo A -> SummaryBundle A --\
repo B -> SummaryBundle B ----> CorpusBundle -> CORPUS_SUMMARY.{md,json}
repo N -> SummaryBundle N --/       |-> repository views
                                  |-> cross-repo candidates
                                  |-> aggregate gaps
```

## Résolution des dépôts

`omega-summary-corpus` accepte trois sources combinables :

- `--workspace DIR` : détection du workspace et de ses enfants directs;
- `--manifest repos.json` : manifeste local, permettant aussi les dépôts privés sans inscrire leur nom dans le code public;
- `--repo DIR` : chemin explicite répétable.

Les chemins absolus ne sont pas sérialisés dans les sorties de corpus; seuls les noms d'affichage et empreintes sont publiés.

## Modèle de sécurité

La couche cross-repo ne possède aucune permission GitHub et n'effectue aucune écriture. Elle travaille sur des checkouts fournis par l'appelant. Le workflow réutilisable n'obtient que `contents: read` et produit un artifact CI.

## Déduplication inter-dépôts

La v0.1 utilise une similarité lexicale Jaccard sur nom/résumé/chemin comme détecteur de **candidats**. Toute relation est `review_only`. Une version future ajoutera embeddings, dépendances, API signatures et preuves de provenance sans auto-fusion.

## Déploiement organisationnel

Après fusion de la PR centrale, chaque dépôt peut appeler `.github/workflows/omega-summary-reusable.yml@main`. La logique reste centralisée; les dépôts satellites ne conservent qu'un petit caller workflow. Les dépôts privés ne sont pas nommés dans le dépôt public central.
