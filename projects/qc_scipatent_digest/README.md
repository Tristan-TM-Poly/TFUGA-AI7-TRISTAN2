# Ω-SCI-PATENT-QC-DIGEST-T

**Digesteur scientifique et brevetaire québécois de Tristan.**

MVP zéro-touch pour ingérer des publications scientifiques associées aux universités du Québec et des brevets québécois/canadiens associés à des inventeurs, propriétaires, demandeurs ou institutions du Québec, puis générer :

- un corpus normalisé;
- des résumés **LOG/CVCD**;
- des scores **OAK**;
- un hypergraphe publications ↔ brevets ↔ chercheurs ↔ universités ↔ domaines ↔ branches Tristan;
- des opportunités de prototypes/revenus/IP;
- une mémoire négative M⁻.

> OAK-safe : ce prototype ne donne pas d'avis juridique, ne prouve pas la validité scientifique d'une publication, et ne conclut pas sur la liberté d'exploitation d'un brevet. Il sert à cartographier, résumer, prioriser et préparer des validations.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
```

## Démo hors-ligne

```bash
python -m qc_scipatent_digest.cli demo --out outputs/demo
```

Résultats générés :

- `outputs/demo/atlas_qc_demo.md`
- `outputs/demo/documents.json`
- `outputs/demo/cvcd_digests.json`
- `outputs/demo/oak_scores.json`
- `outputs/demo/hypergraph.json`
- `outputs/demo/opportunities.json`
- `outputs/demo/m_minus.md`

## Ingestion OpenAlex

```bash
python -m qc_scipatent_digest.cli fetch-openalex \
  --university "Polytechnique Montréal" \
  --from-year 2022 \
  --to-year 2026 \
  --max-records 200 \
  --mailto "your-email@example.com" \
  --out outputs/poly_openalex
```

Le code cherche l'institution dans OpenAlex si `openalex_id` n'est pas déjà présent dans `data/seed/qc_universities.json`, puis récupère les works avec `filter=institutions.id:<ID>`.

## Ingestion CIPO / IP Horizons CSV

Télécharger ou préparer un CSV de brevets CIPO/IP Horizons puis :

```bash
python -m qc_scipatent_digest.cli ingest-cipo-csv \
  --csv path/to/cipo_patents.csv \
  --out outputs/cipo_qc
```

Le parseur est volontairement flexible : il accepte plusieurs noms de colonnes courants (`title`, `inventors`, `applicants`, `ipc_codes`, `claims`, etc.) et filtre par marqueurs québécois (`QC`, Québec, Montréal, Laval, Sherbrooke, etc.).

## Architecture

```text
public sources / CSV / fixtures
  ↓
ingest_openalex.py + ingest_cipo.py
  ↓
normalize.py
  ↓
cvcd.py + oak.py
  ↓
hypergraph.py + opportunity.py
  ↓
report.py + JSON/JSONL/Markdown outputs
```

## Structure des données

Document normalisé :

```json
{
  "id": "...",
  "type": "publication | patent",
  "title": "...",
  "year": 2024,
  "source": "OpenAlex | CIPO/IP Horizons CSV",
  "authors_or_inventors": [],
  "institutions": [],
  "owners_or_assignees": [],
  "topics": [],
  "ipc_cpc": [],
  "claims": [],
  "oak_status": "raw | cleaned | validated"
}
```

## OAK-IP rules

Avant publication publique d'une opportunité :

1. classer l'actif : `open`, `publishable`, `patentable`, `trade_secret`, `licensed`, `blocked`, `unknown`;
2. ne jamais publier une invention potentiellement brevetable avant analyse IP;
3. distinguer brevet déposé, demande publiée, brevet accordé, famille, revendications indépendantes et statut légal;
4. vérifier les homonymes auteur/inventeur et les changements d'affiliation;
5. ne pas utiliser du texte complet sous droit d'auteur sans licence ou exception applicable.

## Commandes canoniques

```text
GO QC-DIGEST DEMO
GO QC-DIGEST POLY
GO QC-DIGEST CIPO
GO QC-DIGEST OAK
GO QC-DIGEST OPPORTUNITIES
GO QC-DIGEST GITHUB
```

## Mode MAX

```bash
python -m qc_scipatent_digest.cli demo-max --out outputs/max
```

Le mode MAX ajoute :

- `bridges.json` et `science_ip_bridges.md` pour liens publication↔brevet;
- `ip_classes.json` pour classification OAK-IP préliminaire;
- `review_queue.md` pour prioriser les vérifications;
- `dashboard.html` pour visualisation locale;
- `hypergraph_mermaid.md` pour graphe Mermaid;
- `digest.sqlite` pour requêtes SQL;
- `opportunity_matrix.csv` pour tableur/CRM.

## Crossref

```bash
python -m qc_scipatent_digest.cli fetch-crossref \
  --query "Polytechnique Montréal batteries" \
  --university "Polytechnique Montréal" \
  --from-year 2022 \
  --to-year 2026 \
  --max-records 200 \
  --mailto "your-email@example.com" \
  --max \
  --out outputs/poly_crossref_max
```

## Plan d'ingestion toutes universités

```bash
python -m qc_scipatent_digest.cli build-plan \
  --from-year 2022 \
  --to-year 2026 \
  --max-records 100 \
  --mailto "your-email@example.com" \
  --out outputs/plan
```
