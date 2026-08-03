# Ω-WEB-HG-T∞ R0.1 — Hypergraphe Web probatoire

Ce module explore des pages Web publiques ou explicitement autorisées et construit un graphe traçable :

```text
site → page → section → lien → preuve → version
```

## Limites de sécurité R0.1

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

`robots.txt` est traité comme une contrainte technique minimale, pas comme une autorisation juridique. Les conditions d'utilisation, licences, droits d'auteur, renseignements personnels et autorisations explicites restent des gates séparés à développer.

## Commandes

```bash
omega-web-hg inspect https://example.org
omega-web-hg crawl https://example.org \
  --output-dir generated/omega_web_hg_t/example \
  --page-budget 100 \
  --delay 1.0
```

`--page-budget 0` retire le plafond de pages du run. Cela ne retire jamais la portée de domaine, `robots.txt`, les limites réseau, le throttling, les contraintes juridiques ou les ressources physiques.

## Sorties

```text
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
```

Chaque page possède un `evidence_id`, un hash SHA-256, les URL demandée/finale/canonique, l'horodatage UTC, le statut HTTP, le type MIME, la taille et certains en-têtes utiles. Les relations page→section et page→page transportent aussi l'identifiant de preuve. Les URL découvertes mais non encore visitées sont matérialisées comme nœuds candidats afin que toutes les arêtes GraphML aient des extrémités existantes.

## Statut épistémique

R0.1 est un crawler HTML statique et un compilateur de provenance. Il ne fournit pas encore :

- WARC conforme;
- rendu JavaScript;
- sitemap/RSS/API;
- PDF et documents bureautiques;
- extraction de claims ou validation d'entailment;
- licence automatique fiable;
- diff temporel ou requêtes conditionnelles persistées;
- crawling distribué.

Ces éléments appartiennent aux versions suivantes et ne doivent pas être revendiqués par R0.1.
