# Ω-SCI-PATENT-QC-DIGEST-T — MAX Roadmap

## Mission

Transformer les publications scientifiques et les brevets liés au Québec en hypergraphe scientifique-IP exploitable pour recherche, prototypes, revenus, collaborations et stratégie de propriété intellectuelle.

## Nouveaux modules MAX

- `bridge.py` : liens hypothétiques publication↔brevet, prior art et transfert technologique.
- `ip_classifier.py` : classification OAK-IP préliminaire : metadata-only, patent caution, trade secret, defensive publication, etc.
- `dashboard.py` : tableau HTML local + graphe Mermaid.
- `export_sqlite.py` : export SQLite interrogeable.
- `ingest_crossref.py` : ingestion Crossref REST API.
- `plans.py` : plan d'ingestion université par université.

## Sorties MAX

- `dashboard.html`
- `digest.sqlite`
- `bridges.json`
- `science_ip_bridges.md`
- `ip_classes.json`
- `review_queue.md`
- `opportunity_matrix.csv`
- `hypergraph_mermaid.md`
- `university_fetch_plan.md/json`

## OAK-Gates obligatoires

1. **OAK-Source** : source autorisée, licence, robots/API, limites de taux.
2. **OAK-Metadata** : DOI, auteurs, affiliations, homonymes, dates.
3. **OAK-IP** : brevet/demande/famille/statut/territoire/revendications/expiration.
4. **OAK-Science** : preuve, méthode, données, code, reproductibilité, citations.
5. **OAK-Tristan** : synergie avec HGFM/CVCD/SAGE/AIT + risque de surinterprétation.
6. **OAK-Publication** : ne pas publier publiquement une invention potentiellement brevetable avant classification.

## Étape suivante recommandée

`GO QC-DIGEST LIVE-POLY-MAX` : exécuter l'ingestion OpenAlex/Crossref pour Polytechnique Montréal, fusionner les résultats avec des CSV CIPO/IP Horizons et générer un rapport OAK-IP confidentiel.
