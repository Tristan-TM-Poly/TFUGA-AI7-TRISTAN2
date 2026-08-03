# Ω-WEB-HG-T∞ R0.4 MAX — absorption probatoire multi-source

## Objectif

Transformer le registre Best Sites en campagne de métadonnées réellement exécutable, reprenable, parallélisable et falsifiable.

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

OpenAlex et NASA sont activés uniquement lorsque leurs variables d’environnement sont présentes. ArXiv reste catalogué mais désactivé jusqu’à revue explicite de sa politique courante.

## Pipeline

```text
catalogue autorisé
→ partition source-disjointe
→ URL bornée par adaptateur
→ requête séquentielle identifiée
→ contrôle taille/statut/rate-limit
→ parsing par liste blanche
→ normalisation minimale
→ déduplication SHA-256 + SQLite/WAL
→ checkpoint atomique
→ receipts JSONL
→ mémoire négative M⁻
→ racines Merkle par shard
→ agrégation dédupliquée
→ racines Merkle globales
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
- configuration de reprise liée à la requête, au shard et aux sources sélectionnées;
- retries exponentiels;
- respect de `Retry-After`;
- débit séquentiel par source;
- taille maximale configurable par réponse;
- erreurs transformées en M⁻ plutôt que supprimées;
- shard vide néanmoins matérialisé et auditable;
- agrégateur qui échoue explicitement si un shard attendu manque.

## Sharding déterministe

Chaque source est affectée à exactement un shard par un hash SHA-256 stable de son `source_id` :

```text
shard(source) = int(SHA256(source_id)[0:16], 16) mod shard_count
```

Cette règle garantit, pour une même version du catalogue :

- partition reproductible;
- aucune source dupliquée entre shards;
- parallélisme sans doublonner volontairement les requêtes;
- reconstruction possible de la répartition;
- détection des shards manquants lors de l’agrégation.

La matrice peut être générée localement :

```bash
omega-web-hg-r04-max matrix --shard-count 4
```

Exécution d’un shard :

```bash
omega-web-hg-r04-max run \
  --output-dir generated/omega_web_hg_r04_max/shard-0 \
  --query "hypergraph fractal mycelial science engineering" \
  --item-budget 5000 \
  --page-size 100 \
  --max-pages-per-source 8 \
  --retries 4 \
  --shard-index 0 \
  --shard-count 4
```

Agrégation :

```bash
omega-web-hg-r04-max aggregate \
  generated/downloaded-shards \
  --output-dir generated/omega_web_hg_r04_max_aggregate \
  --expected-shards 4
```

L’agrégateur déduplique les records, reçus et entrées M⁻ par digest, puis calcule des racines Merkle globales. Il ne déclare `complete: true` que lorsque tous les shards attendus sont présents.

## Capacité

Aucun plafond total permanent n’est codé :

```json
{"permanent_total_cap": null}
```

Chaque exécution reste finie et reçoit ses propres budgets : nombre d’objets, taille de page, pages par source, retries, délai et taille maximale de réponse. Les saturations servent à augmenter, sharder ou restructurer la campagne suivante.

Le workflow GitHub courant utilise quatre shards source-disjoints, chacun avec un budget runtime de 5 000 objets. Cela constitue un budget d’exécution borné, pas une limite architecturale permanente.

## Commandes principales

```bash
omega-web-hg-r04-max catalog --pretty
omega-web-hg-r04-max matrix --shard-count 4
omega-web-hg-r04-max audit generated/omega_web_hg_r04_max/shard-0
```

Variables optionnelles :

```text
OPENALEX_API_KEY
NASA_API_KEY
CROSSREF_MAILTO
NCBI_EMAIL
NCBI_API_KEY
```

Le workflow sharded public n’injecte pas les clés OpenAlex ou NASA; ces adaptateurs sont donc fail-closed et enregistrés comme ignorés lorsque les secrets sont absents.

## Artefacts par shard

```text
campaign-report.json
records.jsonl
receipts.jsonl
mminus.jsonl
checkpoint.json
shard-config.json
campaign.sqlite3
```

## Artefacts agrégés

```text
aggregate-report.json
records.jsonl
receipts.jsonl
mminus.jsonl
```

Les artefacts GitHub Actions sont conservés 30 jours. Aucun corps brut n’est committé dans le dépôt.

## Séparation CI / réseau

Deux workflows distincts réduisent les doubles appels et clarifient les responsabilités :

1. `omega-web-hg-best-sites.yml` : compilation, tests Python 3.10–3.13, validation du schéma, plans déterministes et invariants hors réseau;
2. `omega-web-hg-best-sites-sharded.yml` : quatre shards de métadonnées publiques, audit individuel, téléchargement des artefacts et agrégation Merkle globale.

## Frontières OAK

```text
METADATA != TRUTH
AUTHORITY != INFALLIBILITY
FETCH_SUCCESS != REPUBLICATION_PERMISSION
HASH != SEMANTIC VALIDATION
RECORD COUNT != KNOWLEDGE COMPLETENESS
SHARD COMPLETE != INTERNET COMPLETE
FINITE RUN != PERMANENT CAP
MAX CAMPAIGN != COMPLETE INTERNET ABSORPTION
```
