# Ω-WEB-HG-T∞ R0.4 — Best Sites + MAX absorption

R0.4 ne définit pas « meilleur » par popularité. Une source est priorisée lorsqu'elle combine autorité institutionnelle, provenance, stabilité, interfaces machine, identifiants persistants, conditions de réutilisation lisibles et valeur scientifique ou publique.

## Chaîne cible

```text
catalogue sourcé
→ PolicyGate
→ API / dump / OAI avant crawl HTML
→ métadonnées et licences
→ capture/versionnage
→ normalisation minimale
→ déduplication SQLite/WAL
→ receipts + M⁻ + Merkle
→ absorption R0.3
→ recherche avec URL, locator et evidence_id
```

## Catalogue V1

| Source | Tier | Route préférée | Politique initiale |
|---|---:|---|---|
| Wikimedia / Wikidata | 0 | API + dumps | licences par projet/objet; attribution conservée |
| OpenAlex | 0 | snapshot ou API avec clé | métadonnées uniquement |
| Crossref | 0 | REST public/polite pool | métadonnées; abstraits exclus de MAX |
| PubMed | 0 | E-utilities / baseline | identifiants et métadonnées selon termes PubMed |
| PMC reusable subset | 0 | OAI-PMH | métadonnées; texte seulement si droits explicites |
| arXiv | 0 | API / bulk | désactivé jusqu'à revue de politique courante |
| NIST PDR | 0 | RMM API | métadonnées et jeux ouverts avec termes par record |
| NASA Open APIs | 1 | API avec clé | métadonnées minimisées par service |
| CERN Open Data | 0 | API / OAI | données ouvertes avec licence et citation par record |
| USGS | 1 | FDSN / feeds officiels | métadonnées événementielles |
| ESA CCI | 1 | OpenSearch / catalogues | métadonnées et licences par jeu |
| Gouvernement ouvert Canada | 0 | API catalogue | bilingue, licence ouverte et provenance conservées |

## Plan déterministe sans réseau

```bash
omega-web-hg-r04 audit
omega-web-hg-r04 catalog
omega-web-hg-r04 plan --output-dir generated/omega_web_hg_best_sites_v1
```

Le plan :

- sélectionne les tiers 0 et 1;
- exclut les sources nécessitant une clé absente;
- exclut les sources dont la politique doit encore être revue;
- force `metadata_only`;
- produit un artefact content-addressed sans accès réseau.

## Campagne MAX réelle

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

La campagne possède onze adaptateurs : neuf immédiatement exécutables et deux conditionnels (`OPENALEX_API_KEY`, `NASA_API_KEY`). Les variables `CROSSREF_MAILTO`, `NCBI_EMAIL` et `NCBI_API_KEY` améliorent l'identification ou les limites sans être obligatoires pour le noyau.

## Résilience et preuve

- requêtes séquentielles identifiées;
- `Retry-After` et backoff exponentiel;
- taille maximale par réponse;
- SQLite/WAL;
- checkpoint atomique après chaque requête;
- reprise `--resume`;
- déduplication SHA-256;
- reçus HTTP sans corps brut;
- registre M⁻ pour erreurs, 429, 5xx et parse failures;
- racines Merkle des records, receipts et M⁻;
- rapport OAK content-addressed.

## Données persistées

```text
campaign-report.json
records.jsonl
receipts.jsonl
mminus.jsonl
checkpoint.json
campaign.sqlite3
```

La normalisation exclut les corps HTTP, articles complets, abstracts, explications NASA, listes d'auteurs complètes, PDF, binaires, cookies et secrets.

## Capacité adaptative

`item_budget`, `page_size`, `max_pages_per_source`, `retries` et `max_bytes` bornent une exécution donnée. Aucun plafond total permanent n'est codé :

```json
{"permanent_total_cap": null}
```

Les saturations observées sont conservées dans M⁻ pour augmenter, shard-er ou restructurer la campagne suivante.

## Sources de politique officielles

- Wikimedia API access policy: https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy
- OpenAlex authentication and limits: https://developers.openalex.org/api-reference/authentication
- Crossref REST access and authentication: https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
- PubMed E-utilities policy: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- PMC OAI-PMH: https://pmc.ncbi.nlm.nih.gov/tools/oai/
- NIST RMM API: https://data.nist.gov/rmm/
- NASA Open APIs: https://api.nasa.gov/
- CERN Open Data: https://opendata.cern.ch/docs/about
- USGS FDSN event API: https://earthquake.usgs.gov/fdsnws/event/1
- ESA CCI APIs: https://climate.esa.int/data/apis
- Government of Canada API best practices: https://open.canada.ca/en/working-data-api/best-practices

## Frontières OAK

```text
SOURCE_PRIORITIZED != SOURCE_OBJECTIVELY_BEST
PUBLIC_ACCESS != REPUBLICATION_PERMISSION
METADATA_AVAILABLE != FULL_TEXT_REUSABLE
METADATA_EXTRACTED != CLAIM_TRUE
HIGH_AUTHORITY != ERROR_FREE
HASH != SEMANTIC VALIDATION
LARGE CAMPAIGN != COMPLETE INTERNET
FINITE RUNTIME BUDGET != PERMANENT CAP
```
