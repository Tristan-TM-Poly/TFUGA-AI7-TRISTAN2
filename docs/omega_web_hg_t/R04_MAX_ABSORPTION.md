# Ω-WEB-HG-T∞ R0.4 MAX — absorption probatoire multi-source

## Objectif

Transformer le registre Best Sites en campagne de métadonnées réellement exécutable, reprenable et falsifiable.

La campagne travaille en priorité sur :

- Wikimedia;
- Crossref;
- PubMed;
- PubMed Central OAI;
- NIST Public Data Repository;
- CERN Open Data;
- USGS Earthquake Catalog;
- ESA CCI OpenSearch;
- Gouvernement ouvert Canada.

OpenAlex et NASA sont activés uniquement lorsque leurs variables d’environnement sont présentes.

## Pipeline

```text
catalogue autorisé
→ URL bornée par adaptateur
→ requête séquentielle identifiée
→ contrôle taille/statut/rate-limit
→ parsing par liste blanche
→ normalisation minimale
→ déduplication SHA-256 + SQLite/WAL
→ checkpoint atomique
→ receipts JSONL
→ mémoire négative M⁻
→ racines Merkle
→ rapport OAK
```

## Données conservées

Chaque enregistrement normalisé peut contenir :

- identifiant source;
- titre;
- URL canonique;
- type;
- dates;
- identifiants publics comme DOI, PMID ou CKAN ID;
- licence lorsqu’elle est explicitement exposée;
- topics structurels;
- hash du fragment source;
- identifiant du reçu de requête.

Ne sont pas persistés :

- corps HTTP bruts;
- articles complets;
- abstracts;
- explications NASA;
- champs auteurs complets;
- pièces jointes, PDF ou datasets binaires;
- secrets, clés API ou cookies.

## Résilience

- SQLite en mode WAL;
- déduplication par digest stable;
- checkpoint après chaque requête;
- reprise `--resume` sans rejouer les adaptateurs terminés;
- retries exponentiels;
- respect de `Retry-After`;
- débit séquentiel par source;
- taille maximale configurable par réponse;
- erreurs transformées en M⁻ plutôt que supprimées.

## Capacité

Aucun plafond total permanent n’est codé :

```json
{"permanent_total_cap": null}
```

Chaque exécution reste finie et reçoit ses propres budgets : nombre d’objets, taille de page, pages par source, retries, délai et taille maximale de réponse. Les saturations servent à augmenter ou restructurer la campagne suivante.

## Commandes

```bash
omega-web-hg-r04-max catalog --pretty

omega-web-hg-r04-max run \
  --output-dir generated/omega_web_hg_r04_max \
  --query "hypergraph fractal mycelial science engineering" \
  --item-budget 5000 \
  --page-size 100 \
  --max-pages-per-source 8 \
  --retries 4

omega-web-hg-r04-max audit generated/omega_web_hg_r04_max
```

Variables optionnelles :

```text
OPENALEX_API_KEY
NASA_API_KEY
CROSSREF_MAILTO
NCBI_EMAIL
NCBI_API_KEY
```

## Artefacts

```text
campaign-report.json
records.jsonl
receipts.jsonl
mminus.jsonl
checkpoint.json
campaign.sqlite3
```

## Frontières OAK

```text
METADATA != TRUTH
AUTHORITY != INFALLIBILITY
FETCH_SUCCESS != REPUBLICATION_PERMISSION
HASH != SEMANTIC VALIDATION
RECORD COUNT != KNOWLEDGE COMPLETENESS
FINITE RUN != PERMANENT CAP
MAX CAMPAIGN != COMPLETE INTERNET ABSORPTION
```
