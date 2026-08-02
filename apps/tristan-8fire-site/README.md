# Tristan Web OS R0.3

Application web statique, locale-first et OAK-safe pour explorer le corpus public de Tristan sous forme de théories, claims, preuves déclarées, limites, relations, mémoire négative et prochaines expériences.

## Chaîne centrale

```text
idée
→ théorie
→ claim
→ support déclaré
→ limite / falsification
→ test
→ prototype
→ usage
→ actif ou résultat négatif M⁻
```

R0.3 ne transforme jamais automatiquement un nom, un graphe, un score ou une simulation en preuve.

## Corpus public

- 44 théories structurées;
- 133 claims;
- 268 relations de navigation;
- 44 fiches Markdown générées;
- 307 artefacts déclarés;
- statuts OAK, risques et prochaines actions;
- aucune promotion automatique;
- aucune action externe automatique.

## Vues

- **Tableau de preuve** : métriques, maturité, OAK moyen, risques, centralité et actions.
- **Atlas** : recherche pondérée et filtres par maturité, famille, domaine et risque.
- **Dossier de théorie** : état, claims, limites, voisins, gates et export Markdown.
- **Claim–Evidence Ledger** : registre filtrable de toutes les affirmations.
- **Hypergraphe** : graphe SVG complet ou focal, profondeur 1–3, export GraphML.
- **Evidence Fabric** : dépendances documentaires et concentration des sources.
- **Mémoire négative M⁻** : limites converties en règles anti-erreur.
- **GO Cristallise** : feuille de route par hypothèse, architecture et prototype.
- **Gouvernance** : frontières épistémiques, IP, vie privée et sécurité.

## Exécution locale

Depuis la racine du dépôt :

```bash
python -m http.server 8080 --directory apps/tristan-8fire-site
```

Puis ouvrir le port local 8080. Le protocole `file://` ne permet pas le chargement normal des registres JSON.

## Génération

```bash
python scripts/generate_tristan_web_os_catalog.py
```

Comptes attendus :

```text
44 theories
133 claims
268 relations
44 theory cards
```

## Audit

```bash
python scripts/audit_tristan_web_os_r03.py \
  --output out/tristan-web-os-r03-audit.json
```

## Tests

```bash
python -m pytest -q \
  tests/test_tristan_web_os.py \
  tests/test_tristan_web_os_r03.py
```

## Vérification JavaScript

```bash
find apps/tristan-8fire-site -type f -name '*.js' -print0 \
  | xargs -0 -n1 node --check
```

## Architecture

```text
index.html
├── app.js
├── src/application.js
├── src/router.js
├── src/data-store.js
├── src/search-engine.js
├── src/ui.js
├── src/preferences.js
├── src/exporters.js
├── src/views/*.js
├── data/theories.json
├── data/claims.json
├── data/relations.json
├── app.webmanifest
└── sw.js
```

## Recherche

La recherche globale est accessible avec `Ctrl+K`, `Cmd+K` ou `/`. Elle classe localement théories et claims sans requête réseau externe.

## Exports

Les exports sont générés dans le navigateur uniquement après une action de l’utilisateur :

- JSON;
- CSV des théories;
- CSV des claims;
- Markdown d’une théorie;
- GraphML du graphe affiché.

## Mode hors ligne

Le service worker met en cache le shell applicatif et utilise une stratégie réseau-d’abord pour les registres JSON, avec cache comme secours. Le cache n’est pas une source canonique.

## Accessibilité

- lien d’évitement;
- focus visible;
- navigation clavier;
- région d’annonce `aria-live`;
- thème clair/sombre;
- densité confortable/compacte;
- mouvement réduit;
- mode de couleurs forcées;
- tableaux défilables;
- nœuds du graphe ouvrables au clavier.

## Publication gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Le jeu public exclut par défaut :

- données personnelles sensibles;
- inventions non protégées;
- secrets commerciaux;
- détails dangereux;
- claims sans limite;
- claims sans prochain test;
- actions externes automatiques.

## Frontière épistémique

Un audit vert confirme des invariants déterministes du dépôt. Il ne certifie pas :

- vérité scientifique;
- causalité;
- sécurité physique ou clinique;
- accessibilité complète;
- conformité juridique;
- brevetabilité;
- valeur économique;
- état prêt pour déploiement public.

## Documentation

- `docs/web_os/TRISTAN_WEB_OS_R03_ARCHITECTURE.md`
- `docs/web_os/TRISTAN_WEB_OS_DATA_GOVERNANCE.md`
- `docs/web_os/TRISTAN_WEB_OS_R03_RUNBOOK.md`
- `docs/theory_cards/OMEGA_WEB_TRISTAN_T.md`

## R0.4 proposé

- provenance claim → fichier → lignes → commit → test → résultat;
- manifeste SHA-256 du build;
- diff sémantique des claims;
- liens vers benchmarks réels;
- bilinguisme canonique FR/EN;
- aperçu de déploiement avec audit d’accessibilité;
- premier laboratoire interactif OAKGate.
