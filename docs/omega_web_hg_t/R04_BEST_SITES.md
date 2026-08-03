# Ω-WEB-HG-T∞ R0.4 — Absorption des meilleures sources Internet

R0.4 ne définit pas « meilleur » par popularité. Une source est priorisée lorsqu'elle combine autorité institutionnelle, provenance, stabilité, interfaces machine, identifiants persistants, conditions de réutilisation lisibles et valeur scientifique ou publique.

## Chaîne cible

```text
catalogue sourcé
→ PolicyGate
→ API / dump / OAI avant crawl HTML
→ métadonnées et licences
→ capture R0.2
→ versions et changements
→ absorption R0.3
→ recherche avec URL, locator et evidence_id
```

## Catalogue V1

| Source | Tier | Route préférée | Politique initiale |
|---|---:|---|---|
| Wikimedia / Wikidata | 0 | API + dumps | licences par projet/objet; attribution conservée |
| OpenAlex | 0 | snapshot ou API avec clé | métadonnées uniquement |
| Crossref | 0 | REST polite pool | métadonnées; abstraits prudents |
| PubMed | 0 | E-utilities / baseline | citations et résumés selon termes PubMed |
| PMC reusable subset | 0 | OAI-PMH | texte seulement si droits explicites |
| arXiv | 0 | API / bulk | désactivé jusqu'à revue de politique courante |
| NIST PDR | 0 | RMM API | métadonnées et jeux ouverts avec termes par record |
| NASA Open APIs | 1 | API avec clé | métadonnées et produits selon service |
| CERN Open Data | 0 | API / OAI | données ouvertes avec licence et citation par record |
| USGS | 1 | APIs officielles | métadonnées; termes par produit |
| ESA CCI | 1 | OpenSearch / catalogues | métadonnées et licences par jeu |
| Gouvernement ouvert Canada | 0 | API catalogue | bilingue, licence ouverte et provenance conservées |

## Comportement par défaut

```bash
omega-web-hg-r04 audit
omega-web-hg-r04 catalog
omega-web-hg-r04 plan --output-dir generated/omega_web_hg_best_sites_v1
```

Le plan par défaut :

- sélectionne les tiers 0 et 1;
- exclut les sources nécessitant une clé absente;
- exclut les sources dont la politique doit encore être revue;
- force `metadata_only` pour toutes les sources;
- produit un artefact déterministe sans accès réseau.

Les sources à clé sont ajoutées explicitement :

```bash
OPENALEX_API_KEY=... NASA_API_KEY=... \
omega-web-hg-r04 plan \
  --include-key-required \
  --output-dir generated/omega_web_hg_best_sites_v1
```

L'ouverture des textes réutilisables exige une option séparée :

```bash
omega-web-hg-r04 plan --allow-open-full-text
```

Cette option ne remplace jamais la licence de l'objet, l'attribution, la minimisation des données personnelles ou les restrictions de republication.

## Sources de politique officielles

- Wikimedia API access policy: https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy
- OpenAlex authentication and limits: https://developers.openalex.org/api-reference/authentication
- Crossref REST access and authentication: https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
- PubMed downloads and data terms: https://pubmed.ncbi.nlm.nih.gov/download/
- PMC OAI-PMH: https://pmc.ncbi.nlm.nih.gov/tools/oai/
- NIST Public Data Repository: https://data.nist.gov/pdr/
- NASA Open APIs: https://api.nasa.gov/
- CERN Open Data: https://opendata.cern.ch/docs/about
- USGS APIs: https://www.usgs.gov/products/web-tools/apis
- ESA CCI data access: https://climate.esa.int/en/data/
- Government of Canada API best practices: https://open.canada.ca/en/working-data-api/best-practices

## Frontières OAK

```text
SOURCE_PRIORITIZED != SOURCE_OBJECTIVELY_BEST
PUBLIC_ACCESS != REPUBLICATION_PERMISSION
METADATA_AVAILABLE != FULL_TEXT_REUSABLE
CLAIM_EXTRACTED != CLAIM_TRUE
HIGH_AUTHORITY != ERROR_FREE
SIMILARITY != EQUIVALENCE_OR_PLAGIARISM
LARGE_CAMPAIGN != COMPLETE_INTERNET
```

R0.4 est un routeur de campagne et un registre de politiques. L'exécution réseau massive, la conservation longue durée et la publication de contenus absorbés demeurent des actions séparées gouvernées par budgets, licences, robots, quotas, vie privée et approbation humaine.
