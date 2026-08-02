# Tristan Web OS R0.3 — Runbook

## Exécution locale

Depuis la racine du dépôt :

```bash
python -m http.server 8080 --directory apps/tristan-8fire-site
```

Puis ouvrir localement le port 8080. L’utilisation de `file://` n’est pas supportée pour le chargement des registres JSON.

## Régénération du catalogue

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

La génération doit être déterministe. Une deuxième exécution sans modification des sources ne doit pas produire de diff.

## Audit complet

```bash
python scripts/audit_tristan_web_os_r03.py \
  --output out/tristan-web-os-r03-audit.json
```

Le code de sortie est :

- `0` : aucun invariant bloquant violé;
- `1` : au moins une erreur;
- `2` : avertissement présent avec `--strict-warnings`.

Un audit vert ne certifie pas la science, la sécurité, l’accessibilité, le droit, l’IP ou le marché.

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

## Vérification des sorties générées

```bash
python scripts/generate_tristan_web_os_catalog.py
git diff --exit-code -- \
  apps/tristan-8fire-site/data \
  content/generated
```

Un diff signifie que les sources et les artefacts versionnés ne sont pas synchronisés.

## Vérification réseau

R0.3 ne doit pas contenir d’appel externe dans les modules client :

```bash
grep -RInE 'XMLHttpRequest|sendBeacon|https?://' \
  apps/tristan-8fire-site/src \
  apps/tristan-8fire-site/app.js
```

Les appels `fetch` de R0.3 doivent être limités aux fichiers locaux du site.

## Navigation de validation

Tester au minimum :

1. `#/dashboard`
2. `#/atlas`
3. recherche d’une théorie par symbole;
4. combinaison de plusieurs filtres;
5. ouverture d’une fiche de théorie;
6. ouverture d’un claim;
7. filtre des claims par théorie;
8. graphe complet;
9. graphe focal à profondeur 1, 2 et 3;
10. Evidence Fabric;
11. mémoire négative;
12. feuille de route;
13. page de gouvernance;
14. changement de thème;
15. changement de densité;
16. recherche globale avec `Ctrl+K`;
17. export CSV;
18. export Markdown;
19. export GraphML;
20. rechargement hors ligne après une première visite.

## Accessibilité manuelle

Vérifier :

- navigation clavier complète;
- focus visible;
- lien d’évitement;
- lecture des intitulés par lecteur d’écran;
- absence de piège clavier dans la recherche;
- contraste des thèmes sombre et clair;
- zoom à 200 %;
- largeur mobile;
- préférence de mouvement réduit;
- tableaux défilables horizontalement;
- graphe utilisable au clavier pour ouvrir un nœud.

## Sécurité

Vérifier :

- absence de `innerHTML` appliqué aux données;
- absence de scripts tiers;
- absence de secret ou jeton;
- absence de formulaire d’envoi;
- absence de télémétrie;
- absence de données personnelles;
- absence d’action externe automatique;
- restrictions de publication visibles;
- exports déclenchés uniquement par l’utilisateur.

## Mise à jour des registres

Ne jamais modifier directement les gros fichiers générés comme source principale.

Ordre :

```text
modifier source compacte
→ lancer générateur
→ inspecter diff
→ lancer audit
→ lancer tests
→ réviser les claims et limites
→ commit
→ CI
→ revue humaine
```

## Ajout d’une théorie

Une nouvelle théorie publique exige :

- identifiant stable `omega-...`;
- symbole;
- résumé public réduit;
- domaines;
- maturité;
- preuve déclarée;
- état OAK;
- prochaine action;
- risques;
- source;
- classification IP;
- quatre gates;
- au moins trois claims : portée, limite et prochain test;
- relations de navigation contrôlées.

Les comptes fixes du générateur et de l’audit doivent être mis à jour intentionnellement. Ils ne doivent pas être contournés avec un seuil large.

## Ajout d’une relation

Avant d’ajouter une relation :

- définir le type exact;
- rédiger une rationale;
- confirmer les deux nœuds;
- préciser la direction;
- conserver `evidence_required=true`;
- conserver `public_scope=navigation`;
- éviter les doublons sémantiques;
- ne pas transformer une proximité conceptuelle en causalité.

## Déploiement

R0.3 ne contient aucune autorisation implicite de déploiement public. Avant déploiement :

1. revue IP;
2. revue vie privée;
3. revue de sécurité;
4. revue des claims;
5. validation de l’hébergement;
6. en-têtes de sécurité;
7. politique de cache;
8. domaine et certificats;
9. mécanisme de retrait;
10. responsable humain identifié.

## Retour arrière

Le site est statique. Le retour arrière recommandé consiste à redéployer un commit antérieur connu comme valide.

Ne pas :

- effacer l’historique automatiquement;
- forcer une branche sans inspection;
- modifier les données générées directement en production;
- masquer une erreur de claim sans entrée M⁻;
- réutiliser un cache de version incompatible.

## Promotion R0.3 → R0.4

Conditions minimales :

- CI R0.3 verte;
- zéro erreur d’intégrité;
- audit accessibilité documenté;
- audit de sécurité statique;
- provenance commit/ligne pour les claims prioritaires;
- au moins une divergence code-document détectée automatiquement;
- aucune donnée sensible dans la projection publique;
- décision humaine explicite sur le déploiement.
