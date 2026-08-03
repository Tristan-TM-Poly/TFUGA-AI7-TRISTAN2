# Ω-WEB-HG-T∞ — Hypergraphe Web probatoire

Ce module explore des pages Web publiques ou explicitement autorisées et construit un graphe traçable :

```text
site → page → section → lien → preuve → version → changement → claim candidat → requête
```

## R0.1 — noyau statique sûr

- HTTP(S) seulement;
- domaines explicitement autorisés;
- blocage des adresses privées, locales, réservées et non résolues;
- aucune authentification, aucun cookie, aucun contournement de CAPTCHA, paywall ou contrôle d'accès;
- respect de `robots.txt`, avec refus conservateur si la politique est indéterminable;
- validation de chaque redirection avant qu'elle soit suivie;
- délai minimal par domaine;
- taille maximale par réponse;
- corps bruts optionnels, séparés des graphes dérivés;
- un résultat extrait n'est ni une certification factuelle ni une permission de republication.

`robots.txt` est traité comme une contrainte technique minimale, pas comme une autorisation juridique. Les conditions d'utilisation, licences, droits d'auteur, renseignements personnels et autorisations explicites restent des gates séparés.

```bash
omega-web-hg inspect https://example.org
omega-web-hg crawl https://example.org \
  --output-dir generated/omega_web_hg_t/example \
  --page-budget 100 \
  --delay 1.0
```

## R0.2 MAX — observatoire incrémental

R0.2 ajoute :

- frontière SQLite persistante avec leases, reprise et recrawl;
- requêtes conditionnelles `ETag` / `Last-Modified` et traitement `304`;
- découverte par sitemaps, index de sitemaps, RSS, Atom, JSON Feed, `robots.txt`, HTML et en-têtes `Link`;
- respect de `noarchive`, `nofollow` et `X-Robots-Tag`;
- objets bruts adressés par SHA-256 et capture WARC 1.1;
- versions et changements `ADDED`, `MODIFIED`, `UNCHANGED`, `NOT_MODIFIED`, `REMOVED`, `MISSING`;
- hypergraphe v2, GraphML, provenance JSON-LD inspirée de PROV-O;
- snapshots SQLite, diff inter-runs, audit structurel et schémas JSON.

```bash
omega-web-hg-r02 crawl https://example.org \
  --output-root generated/omega_web_hg_t_r02/example \
  --resource-budget 1000 \
  --max-depth 12 \
  --max-frontier 100000

omega-web-hg-r02 state generated/omega_web_hg_t_r02/example
omega-web-hg-r02 audit generated/omega_web_hg_t_r02/example/runs/<run_id>
omega-web-hg-r02 diff <run-précédent> <run-courant> --output diff.json
```

Une valeur `0` retire le plafond fini correspondant. Les contraintes de portée, réseau, robots, débit, stockage, droit et capacité physique restent actives. La spécification détaillée est dans [`R02_MAX.md`](R02_MAX.md).

## R0.3 MAX — absorption et recherche probatoires

R0.3 travaille hors réseau sur un run R0.2 :

- segmentation déterministe des sections en phrases candidates;
- chaque candidate garde `page_id`, `section_id`, `evidence_id`, URL et locator;
- hash SHA-256 du texte;
- déduplication exacte;
- déduplication proche par SimHash 64 bits, bandes et distance de Hamming;
- hypergraphe `section → claim_candidate → evidence`;
- index SQLite avec FTS5 lorsque disponible et fallback portable;
- requêtes filtrables par type retournant texte, URL, locator, preuve, score et métadonnées;
- audit des références, arêtes et couverture d'index.

```bash
omega-web-hg-r03 build <run-r02> \
  --output-dir generated/omega_web_hg_t_r03/corpus

omega-web-hg-r03 query generated/omega_web_hg_t_r03/corpus \
  "preuve reproductible" \
  --kind claim_candidate \
  --limit 20

omega-web-hg-r03 audit generated/omega_web_hg_t_r03/corpus
```

La spécification détaillée est dans [`R03_ABSORPTION_MAX.md`](R03_ABSORPTION_MAX.md).

## Sorties principales

```text
# R0.1
manifest.json
pages.jsonl
sections.jsonl
edges.jsonl
evidence.jsonl
policy-decisions.jsonl
url-candidates.jsonl
hypergraph.json
hypergraph.graphml
oak-report.json
raw/<préfixe>/<sha256>.html

# R0.2
discoveries.jsonl
document-metadata.jsonl
versions.jsonl
changes.jsonl
hypergraph-v2.json
hypergraph-v2.graphml
provenance.jsonld
archive.warc
state.snapshot.sqlite3
objects/sha256/...

# R0.3
claim-candidates.jsonl
duplicates.jsonl
absorption-hypergraph.json
absorption-report.json
search.sqlite3
```

Chaque page possède un `evidence_id`, un hash SHA-256, les URL demandée/finale/canonique, l'horodatage UTC, le statut HTTP, le type MIME, la taille et certains en-têtes utiles. Les relations transportent les identifiants de preuve lorsque disponibles. Les URL découvertes mais non encore visitées sont matérialisées comme nœuds candidats afin que les arêtes GraphML aient des extrémités existantes.

## Statut épistémique et limites

Un `claim_candidate` est une phrase extraite, pas une proposition démontrée. La similarité ne prouve ni vérité, ni entailment, ni plagiat, ni antériorité, ni droit de republication.

Le système ne fournit pas encore :

- rendu JavaScript ou interaction navigateur;
- authentification ou collecte de contenu privé;
- PDF et documents bureautiques;
- corroboration/contradiction sémantique certifiée;
- classification juridique automatique fiable;
- crawling distribué multi-machine;
- garantie absolue contre toutes les variantes de DNS rebinding;
- certification de rejeu WARC indépendante.

Aucun de ces éléments ne doit être revendiqué sans nouvelle implémentation, tests et validation OAK.
