# Tristan Web OS R0.3 — Architecture applicative

## Statut

R0.3 est une application web statique, locale-first et OAK-safe. Elle rend navigables les registres publics générés par R0.2 sans transformer leur présence dans le dépôt en preuve scientifique.

## Objectif

```text
corpus canonique
→ sources compactes révisables
→ générateur déterministe
→ registres publics JSON
→ audit de structure et de provenance
→ application multi-vues
→ export local explicite
```

L’application doit répondre à six questions pour chaque objet :

1. Qu’est-ce que c’est?
2. Quel est son statut actuel?
3. Qu’est-ce qui le supporte?
4. Qu’est-ce qui pourrait le limiter ou le réfuter?
5. Quelle est la prochaine action vérifiable?
6. Peut-il être publié sans exposer IP, vie privée ou capacité risquée?

## Couches

### 1. Génération

- `scripts/tristan_web_catalog_seed_01.py` à `04.py` : sources publiques compactes.
- `scripts/generate_tristan_web_os_catalog.py` : compilation déterministe.
- `content/generated/` : fiches et index révisables.
- `apps/tristan-8fire-site/data/` : registres consommés par l’application.

### 2. Contrats

- `schemas/tristan_web_os/theory.schema.json`
- `schemas/tristan_web_os/claim.schema.json`
- `schemas/tristan_web_os/relation.schema.json`

Les schémas déclarent les invariants principaux. L’audit Python applique également les contraintes inter-fichiers et les règles OAK qui ne sont pas facilement exprimables en JSON Schema.

### 3. Stockage client

`src/data-store.js` charge en parallèle :

- 44 théories;
- 133 claims;
- 268 relations.

Il construit ensuite :

- index `theoryById`;
- index `claimById`;
- claims groupés par théorie;
- relations entrantes et sortantes;
- voisinages;
- statistiques agrégées;
- feuille de route heuristique.

Aucune base de données distante n’est requise pour R0.3.

### 4. Routage

`src/router.js` interprète les routes par fragment :

```text
#/dashboard
#/atlas?q=...
#/theory/<id>
#/claims?theory=<id>
#/claim/<id>
#/graph/<focus>?depth=2
#/evidence
#/mminus
#/roadmap
#/about
```

Le fragment conserve les recherches et filtres dans l’URL sans serveur applicatif.

### 5. Recherche

`src/search-engine.js` applique :

- normalisation Unicode;
- retrait des accents pour la recherche;
- tokenisation;
- pondération par champ;
- classement déterministe.

Les symboles, titres et identifiants reçoivent un poids supérieur aux résumés. La recherche est un mécanisme de navigation, pas un score de vérité ni de fertilité scientifique.

### 6. Vues

| Vue | Fonction |
|---|---|
| Dashboard | métriques, maturité, OAK moyen, risques, centralité, actions |
| Atlas | recherche et filtres multi-dimensionnels |
| Theory | dossier complet d’une branche |
| Claims | Claim–Evidence Ledger filtrable |
| Claim | contrat épistémique d’une affirmation |
| Graph | voisinage et graphe public exportable |
| Evidence | dépendances documentaires et concentration des sources |
| M⁻ | limites transformées en règles anti-erreur |
| Roadmap | actions classées pour cristallisation |
| About | gouvernance et frontières du système |

### 7. Interface sûre

`src/ui.js` interdit explicitement l’injection de HTML arbitraire. Les données du corpus sont écrites avec `textContent` ou des nœuds DOM construits localement.

L’application n’utilise :

- aucun CDN;
- aucune police distante;
- aucun tracker;
- aucun script tiers;
- aucun appel API externe;
- aucune télémétrie.

### 8. Exports

`src/exporters.js` génère localement :

- JSON filtré;
- CSV des théories;
- CSV des claims;
- fiche Markdown d’une théorie;
- GraphML du graphe affiché.

L’export exige une action utilisateur. Il ne publie rien automatiquement et n’envoie aucun contenu à un service externe.

### 9. Mode hors ligne

`sw.js` met en cache le shell applicatif. Pour les registres JSON, la stratégie est réseau d’abord et cache en secours afin d’éviter de servir indéfiniment un corpus ancien lorsque le réseau est disponible.

Le service worker ne transforme pas le cache en source canonique. Le dépôt et les fichiers générés restent les références versionnées.

## Invariants

```text
PUBLIC = OAKGate ∧ IPGate ∧ PrivacyGate ∧ SecurityGate
```

```text
relation affichée ≠ causalité démontrée
score OAK ≠ probabilité de vérité
claim documenté ≠ claim validé
prototype ≠ produit qualifié
source interne ≠ réplication indépendante
```

## Frontières R0.3

R0.3 ne fournit pas encore :

- authentification;
- coffre IP;
- espace partenaire;
- édition du canon dans le navigateur;
- collaboration temps réel;
- backend de recherche;
- provenance page/bbox de PDF;
- validation cryptographique des builds;
- traduction canonique FR/EN complète;
- déploiement de production autorisé.

Ces absences doivent rester visibles pour éviter de confondre architecture et service exploité.

## Évolution recommandée

### R0.4 — Provenance exécutable

- claim → fichier → plage de lignes → commit → test → résultat;
- hash SHA-256 des sources et sorties;
- manifeste de build;
- diff sémantique des claims;
- détection automatique des pages obsolètes.

### R0.5 — Laboratoires

- OAKGate interactif;
- visualiseur FFWT;
- analyseur de résidus;
- explorateur de transformées;
- démonstrations avec données synthétiques clairement identifiées.

### R1.0 — Asset OS

- séparation publique/partenaire/privée/IP;
- rôles et approbations;
- packages de collaboration;
- pipelines de produit et de licence;
- publication contrôlée.
