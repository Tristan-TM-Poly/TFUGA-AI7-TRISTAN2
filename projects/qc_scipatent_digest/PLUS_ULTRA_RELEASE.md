# Ω-SCI-PATENT-QC-DIGEST-T v0.3 PLUS ULTRA

## Statut

Version locale générée et testée : **v0.3 PLUS ULTRA**.

Cette version transforme le MVP/MAX en noyau réutilisable pour recherche, veille, IP, prototypes, revenus et canon TFUGA/SAGE.

## Ajouts v0.3

### 1. Reusable pipeline kernel

Nouveaux objets :

- `PipelineConfig`
- `PipelineResult`
- `DigestPipeline`

But : exécuter le digesteur depuis CLI, notebook, CI, agent AIT/SAGE ou futur service API.

### 2. PLUS ULTRA command

Commande locale validée :

```bash
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v03
```

Sorties générées :

- `pipeline_config.json`
- `pipeline_summary.json`
- `entity_clusters.json`
- `entity_resolution_warnings.md`
- `release_assessment.json`
- `release_assessment.md`
- `reuse_blueprints.json`
- `reuse_blueprints.md`
- `canon_pack/dct_cards.json`
- `canon_pack/dct_cards.md`
- plus tous les outputs MAX : dashboard, SQLite, bridges, review queue, opportunities, hypergraph.

### 3. OAK release gates

Nouveau module : `oak_gates.py`.

Gates :

- `OAK-Source`
- `OAK-IP`
- `OAK-Science`

Résultats possibles :

- `pass`
- `pass_with_caution`
- `review_required`
- `blocked`

Règle : aucune publication publique, pitch commercial, brevet, divulgation ou contact sensible sans revue OAK-IP/OAK-Science.

### 4. Entity resolution layer

Nouveau module : `entity_resolution.py`.

Fonctions :

- normalisation noms/auteurs/inventeurs/institutions;
- clés de blocage;
- clustering approximatif;
- warnings pour homonymes et variantes.

But : réduire les faux liens publication↔brevet causés par homonymes, variantes institutionnelles ou changements d'affiliation.

### 5. Canon export DCT++

Nouveau module : `canon_export.py`.

Produit :

- DCT++ cards pour documents;
- DCT++ cards pour opportunités;
- export JSON/Markdown.

But : transformer les résultats en objets réutilisables dans TFUGA/SAGE/HGFM/OAK.

### 6. Reuse blueprints

Nouveau module : `reuse_blueprints.py`.

Blueprints :

- Digest API Kernel;
- Atlas Science-IP Québec;
- IP Opportunity Miner;
- OAK Research Assistant.

Chaque blueprint contient : but, inputs, outputs, formes réutilisables, OAK locks, next build et valeur économique/scientifique.

### 7. GitHub CI plan

Workflow local préparé :

```text
.github/workflows/qc_scipatent_digest_ci.yml
```

Tests validés localement :

```bash
python -m pytest -q
# 2 passed
```

## Résultat démo v0.3

Sur fixtures Polytechnique/OpenAlex + CIPO Québec :

- 6 documents;
- 6 opportunités;
- 9 bridges science↔IP;
- DCT++ canon pack;
- OAK release assessment;
- reuse blueprints;
- dashboard + SQLite + hypergraph.

## OAK-SAFE

Cette version est un moteur de cartographie, priorisation et génération d'opportunités. Elle ne donne pas :

- avis juridique;
- liberté d'exploitation;
- preuve de validité brevet;
- preuve de reproductibilité scientifique;
- autorisation de publication d'invention brevetable.

Avant toute sortie publique : classer `open | publishable | patentable | trade_secret | licensed | blocked | unknown`.

## Package artifact local

Artifact local généré :

```text
qc_scipatent_digest_plus_ultra.zip
SHA-256: e48aed805f9aa62d6c665ef137189aeeb1bac2504bd6c27185146636e93749ff
```

## Prochaine étape GitHub idéale

Quand on veut basculer de PR scaffold à dépôt source complet :

1. ajouter tout le source tree sous `projects/qc_scipatent_digest/`;
2. activer la GitHub Action;
3. faire tourner `plus-ultra` en CI;
4. transformer les opportunités en issues GitHub OAK-gated;
5. garder les données live et IP sensibles hors repo public.
