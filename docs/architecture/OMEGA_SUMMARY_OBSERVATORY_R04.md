# Ω-SUMMARY-FRACTAL-T∞ R0.4 — Observatory, Identity & Query

## But

R0.4 transforme le résumeur longitudinal R0.3 en **surface d'observabilité interrogable** du corpus.

La chaîne devient :

```text
repository state
  -> D0..D9 summary
  -> evidence graph
  -> longitudinal hash chain
  -> DeltaSummary
  -> identity continuity candidates
  -> transversal queries
  -> corpus dashboard
```

L'architecture reste strictement OAK-safe : une observation Git ne devient jamais automatiquement une revendication scientifique, économique, juridique ou IP.

## 1. Identity Continuity

### Problème

Un système peut être :

- renommé;
- déplacé;
- extrait d'un dépôt;
- recopié;
- forké;
- réorganisé.

Une comparaison purement fondée sur le chemin produit alors artificiellement :

```text
SYSTEM_REMOVED(old_name)
SYSTEM_ADDED(new_name)
```

même lorsque les deux arbres peuvent représenter une continuité plausible.

### Signature content-addressed

Pour un nœud système `X`, le moteur construit :

```text
H_X = SHA256(sorted(unique(evidence.sha256)))
```

La signature ignore le chemin du système et utilise uniquement les hashes des artefacts de preuve déjà observés.

### Appariement

Deux systèmes retiré/ajouté sont proposés comme candidats lorsque :

1. leurs signatures exactes sont identiques; ou
2. le Jaccard des hashes de preuve dépasse `min_overlap`.

```text
J(A,B) = |A intersection B| / |A union B|
```

### Invariants

Même une signature exacte reste :

```text
classification = rename-or-move-candidate
status = review_required
automatic_rewrite = false
```

Raison : du contenu identique peut être copié, forké, vendored ou réutilisé légitimement.

Le moteur indique aussi si le couplage est `one_to_one`, mais cela ne donne aucune autorité de réécriture.

### CLI

```bash
omega-summary identity previous_d9.json current_d9.json \
  --min-overlap 0.80 \
  --output-dir .omega/identity
```

Sorties :

- `IDENTITY_CONTINUITY.json`;
- `IDENTITY_CONTINUITY.md`.

## 2. Transversal Query Engine

### Objet

Le moteur de requête accepte trois surfaces :

1. résumé de dépôt D0-D9;
2. `CORPUS_SUMMARY.json`;
3. `SUMMARY_HISTORY.json` / `CORPUS_INDEX.json`.

Les filtres peuvent porter sur :

- texte;
- type de nœud;
- statut;
- relation;
- dépôt;
- cristallisation structurelle minimale/maximale;
- limite de résultats.

### Exemples

```bash
omega-summary query summary_d9_oak.json \
  --kind system \
  --status tested
```

```bash
omega-summary query CORPUS_SUMMARY.json \
  --repository physics \
  --min-crystallization 0.8
```

```bash
omega-summary query SUMMARY_HISTORY.json \
  --status implemented \
  --max-crystallization 0.6
```

```bash
omega-summary query summary_d9_oak.json \
  --relation DEPENDS_ON \
  --text proof
```

### Sorties

- JSON stdout par défaut;
- `QUERY_RESULTS.json` et `QUERY_RESULTS.md` avec `--output-dir`.

### Boundary

Un classement par `C_struct` signifie seulement que davantage d'artefacts structurels observables sont présents. Il ne signifie pas que la théorie est meilleure, plus vraie, plus originale ou plus vendable.

## 3. Corpus Dashboard

Le dashboard agrège sans fusionner :

- nombre de systèmes;
- nombre de dépôts;
- distributions de statuts;
- nombre de relations observées;
- cristallisation structurelle moyenne;
- dette structurelle moyenne;
- systèmes implémentés sans tests;
- systèmes implémentés sans CI liée;
- systèmes implémentés sans contrat machine;
- systèmes les plus cristallisés structurellement;
- systèmes avec la dette la plus élevée;
- tendances longitudinales lorsqu'un index est disponible.

### CLI

```bash
omega-summary dashboard summary_d9_oak.json \
  --index-file SUMMARY_HISTORY.json \
  --output-dir .omega/dashboard
```

### Zéro-touch

`omega-summary all-depths` produit désormais automatiquement :

```text
output/
  dashboard/
    CORPUS_DASHBOARD.json
    CORPUS_DASHBOARD.md
```

Le mode multi-dépôts fait de même à partir de :

```text
CORPUS_SUMMARY.json + CORPUS_INDEX.json
```

## 4. Contrats machine-readable R0.4

R0.4 ajoute :

- `omega_summary_identity.schema.json`;
- `omega_summary_query.schema.json`;
- `omega_summary_dashboard.schema.json`.

Ils s'ajoutent aux contrats R0.1-R0.3 et sont tous vérifiés par le même OAKBench.

## 5. OAKBench R0.4

Le tribunal exécute notamment :

- Python 3.10-3.13;
- validation Draft 2020-12 de tous les schémas `omega_summary_*`;
- compilation;
- tests summary/corpus/lineage/delta/index/export/relations/R0.4;
- double génération D0-D9 et diff déterministe;
- chronologie Git;
- graphe de preuves;
- dette de preuve;
- super-kernels review-only;
- DeltaSummary;
- chaîne longitudinale;
- GraphML/JSONL;
- Identity Continuity;
- Query Engine;
- dashboard dépôt;
- dashboard corpus;
- audit des SHA GitHub Actions;
- artefact CI de preuve.

## 6. Questions que R0.4 permet de poser

Le système peut désormais servir de substrat à des questions comme :

```text
Quels systèmes sont tested ?
Quels systèmes sont implemented mais sans CI ?
Quels systèmes dépassent C_struct = 0.8 ?
Quels systèmes dépendent de tel kernel ?
Quels systèmes ont probablement été renommés ?
Quels dépôts concentrent la dette structurelle ?
Quels systèmes améliorent leur cristallisation sur plusieurs runs ?
Quels systèmes stagnent structurellement ?
```

Ces questions deviennent des requêtes machine-readable plutôt que des lectures manuelles de centaines de dossiers.

## 7. Ce que R0.4 ne fait pas

R0.4 ne décide pas automatiquement :

- qu'un renommage est certain;
- que deux systèmes sont identiques;
- qu'un système doit être supprimé ou fusionné;
- qu'un benchmark logiciel valide une loi scientifique;
- qu'une chronologie Git établit une priorité scientifique ou IP;
- qu'un score élevé implique une valeur commerciale;
- qu'un dashboard remplace une revue humaine.

## 8. Invariant directeur

```text
OBSERVE MORE != CLAIM MORE
```

Plus l'observatoire devient puissant, plus les frontières entre :

```text
observation
inférence
hypothèse
validation
preuve
```

doivent rester explicites.
