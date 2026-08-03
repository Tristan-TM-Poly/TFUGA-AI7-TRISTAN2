# Ω-WEB-HG-T∞ R0.2 MAX — Observatoire Web incrémental probatoire

R0.2 transforme le crawler HTML R0.1 en campagne persistante, reprenable et temporelle.

## Pipeline

```text
seed + URLs déjà connues
  → PolicyGate / robots / réseau public
  → frontière SQLite louée et reprenable
  → HTTP conditionnel ETag / Last-Modified
  → HTML + sitemap + RSS/Atom + JSON Feed + robots Sitemap + Link headers
  → sections + métadonnées + JSON-LD digests
  → objets SHA-256 + WARC 1.1
  → versions + changements
  → hypergraphe v2 + PROV-O JSON-LD
  → audit OAK + état reproductible
```

## Commandes

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

Une valeur `0` retire le plafond fini correspondant pour `resource-budget`, `max-depth` ou `max-frontier`. Les contraintes de portée, réseau, robots, débit, stockage, droit et capacité physique restent actives.

## Découverte

R0.2 découvre des URL par :

- liens HTML;
- `<link rel="sitemap">`;
- `<link rel="alternate" type="application/rss+xml|application/atom+xml|application/feed+json">`;
- en-têtes HTTP `Link`;
- lignes `Sitemap:` de `robots.txt`;
- `/sitemap.xml` et index de sitemaps;
- RSS 2.0, Atom et JSON Feed;
- campagnes précédentes conservées dans SQLite.

## Provenance

Chaque run écrit notamment :

```text
manifest.json
pages.jsonl
sections.jsonl
edges.jsonl
evidence.jsonl
discoveries.jsonl
document-metadata.jsonl
versions.jsonl
changes.jsonl
hypergraph-v2.json
hypergraph-v2.graphml
provenance.jsonld
archive.warc
state.snapshot.sqlite3
oak-report.json
objects/sha256/...
```

L'hypergraphe v2 matérialise les runs, pages, sections, candidats, versions, preuves, métadonnées, changements et décisions de politique. `provenance.jsonld` relie les versions aux preuves et au run avec des relations inspirées de PROV-O.

## Politique d'archivage

- `noarchive` supprime le stockage du corps brut et remplace la réponse WARC par une notice de métadonnées de suppression;
- `nofollow` empêche l'expansion des liens HTML de la page;
- `X-Robots-Tag` est fusionné aux directives `<meta name="robots">`;
- les contenus publics ne sont pas automatiquement libres de republication;
- les captures WARC restent soumises aux politiques de conservation, droits d'auteur, vie privée et autorisations.

## Limites déclarées

R0.2 n'est pas encore un navigateur JavaScript, un moteur de contournement, un collecteur authentifié, un classificateur juridique fiable, un extracteur de claims certifiés ou un cluster distribué. La résistance à toutes les variantes de DNS rebinding et la conformité de rejeu WARC inter-outils demandent encore des validations indépendantes.
