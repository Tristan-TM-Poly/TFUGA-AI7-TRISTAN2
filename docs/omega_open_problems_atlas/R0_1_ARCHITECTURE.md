# Ω-OPEN-PROBLEMS-ATLAS-T∞ R0.1

## Atlas sans plafond des problèmes, conjectures, concours et défis de Tristan

**Statut :** architecture logicielle de recherche, seed vérifiable, aucune solution mathématique revendiquée.

## 1. Objet

Le système transforme des problèmes mathématiques provenant de sources identifiées en objets versionnés, comparables et falsifiables. Il vise à conserver durablement :

- les énoncés normalisés;
- les sources et dates de vérification;
- les hypothèses et quantificateurs;
- les résultats connus;
- les relations entre problèmes, méthodes et lemmes;
- les expériences numériques;
- les contre-exemples;
- les formalisations;
- les résidus et échecs M−.

Le nombre d'objets peut croître sans plafond total permanent, mais chaque exécution reste bornée par les ressources, les licences, la qualité des sources et la capacité de vérification.

## 2. Frontière épistémique

```text
SOURCE_REPORTED_OPEN != INDEPENDENTLY_CHECKED_OPEN
FINITE_TEST != UNIVERSAL_PROOF
GENERATED_CELL != OPEN_PROBLEM
NUMERICAL_PATTERN != THEOREM
FORMAL_SKELETON != COMPLETED_FORMAL_PROOF
MANY_ADDITIONS != MATHEMATICAL_PROGRESS
```

R0.1 contient sept fiches Clay : six sont enregistrées comme `SOURCE_REPORTED_OPEN`; Poincaré est conservé comme benchmark résolu. Même une source institutionnelle ne remplace pas une recherche bibliographique indépendante au moment d'investir un effort majeur.

## 3. ProblemGenome

Chaque problème réel doit posséder au minimum :

```text
problem_id
canonical title
normalized statement
source identifier and locator
kind
mathematical domains
open-status state
research epistemic state
last status check when independently checked
human-review boundary
finite-computation boundary
solution-claim flag
```

Les énoncés et enregistrements ont des empreintes SHA-256 déterministes. Le registre bloque les identifiants dupliqués et les énoncés normalisés identiques.

## 4. Machine d'état

```text
DISCOVERED
→ SOURCE_VERIFIED
→ OPEN_STATUS_CHECKED
→ NORMALIZED
→ LITERATURE_BASELINED
→ DECOMPOSED
→ COMPUTATIONALLY_PROBED
→ PARTIAL_PROGRESS
→ INDEPENDENTLY_REPRODUCED
→ FORMALIZED_OR_PEER_REVIEWED
→ CANON_CANDIDATE
```

États de statut ouvert :

```text
DISCOVERED_UNVERIFIED
SOURCE_REPORTED_OPEN
INDEPENDENTLY_CHECKED_OPEN
PARTIALLY_RESOLVED
RESOLVED
STATUS_DISPUTED
STALE_SOURCE
```

## 5. OAKGate

Le gate est fail-closed. Il bloque notamment :

- l'absence d'identité, d'énoncé ou de provenance;
- la suppression de la règle « calcul fini ≠ preuve universelle »;
- la suppression de la revue humaine;
- la promotion automatique d'un résultat en solution;
- la promotion d'un statut rapporté par une source en statut ouvert indépendamment vérifié.

Décisions possibles :

```text
BLOCK
DISCOVERY_ONLY
RESEARCH_READY
RESULT_REVIEW_REQUIRED
CANON_REVIEW_REQUIRED
```

## 6. Seed-1024

Le checkpoint R0.1 matérialise exactement :

```text
32 domaines × 32 opérateurs de recherche = 1 024 cellules
```

Ces cellules sont des **emplacements de recherche adressables**. Elles ne sont pas comptées comme problèmes ouverts vérifiés. Chaque cellule attend un ProblemGenome sourcé avant de devenir une campagne réelle.

Exemples d'opérateurs :

- normaliser l'énoncé;
- auditer les quantificateurs;
- chercher une formulation équivalente;
- classifier les petites dimensions;
- rechercher des contre-exemples;
- dériver des bornes;
- construire un substitut fini;
- formaliser les définitions;
- auditer les échanges de limites;
- cartographier les transferts de méthodes;
- enregistrer les approches échouées.

## 7. Réservoirs initiaux

Le catalogue source R0.1 reconnaît les classes suivantes :

- Clay Millennium Prize Problems;
- AIM Problem Lists;
- Erdos Problems;
- MathOverflow `open-problems`;
- sections de problèmes dans les articles et actes de conférences;
- archives de concours et benchmarks;
- défis scientifiques et algorithmiques.

Chaque adaptateur futur doit respecter attribution, licence, provenance, limites d'API, règles de concours et dates de statut.

## 8. Portefeuille recommandé

Le portefeuille ne doit pas contenir uniquement des problèmes monumentaux :

```text
6 grands programmes Clay ouverts
+ problèmes intermédiaires spécialisés
+ cas particuliers attaquables
+ contre-exemples et améliorations de bornes
+ concours à retour rapide
+ formalisation de résultats connus
+ benchmarks computationnels
```

Le transfert de méthode est une hypothèse testable, pas une conséquence automatique de la proximité lexicale ou thématique.

## 9. Commandes

```bash
python -m omega_open_problems_atlas.cli seed-1024 \
  --output /tmp/open-problems-seed-1024.json

python -m omega_open_problems_atlas.cli validate-clay \
  --output /tmp/open-problems-clay-report.json

pytest -q tests/test_omega_open_problems_atlas.py
```

## 10. Successeur R0.2 MAX

R0.2 est matérialisé dans [`R0_2_MAX_ARCHITECTURE.md`](R0_2_MAX_ARCHITECTURE.md). Il ajoute :

1. ingestion de snapshots multi-sources en lecture locale;
2. provenance et décisions de licence;
3. déduplication exacte et lexicale;
4. registre SQLite WAL transactionnel;
5. 64 opérateurs d'obligations de preuve;
6. 128 cartes de méthodes;
7. graphes de transfert avec round-trip obligatoire;
8. preuves Merkle et reçus d'évidence;
9. registres de concours séparés des problèmes ouverts;
10. audits Lean, Coq et Isabelle;
11. frontière logique de 268 435 456 cellules;
12. campagne logicielle durable de 250 000 obligations.

Ces volumes sont des preuves de capacité logicielle, pas des découvertes mathématiques.

## 11. Non-revendications permanentes

R0.1 et R0.2 ne démontrent pas :

- que les cellules générées sont des problèmes ouverts vérifiés;
- qu'un problème Clay a été résolu;
- qu'un problème reste ouvert uniquement parce qu'une page le dit;
- qu'une simulation numérique constitue une preuve;
- qu'un grand volume GitHub constitue une découverte;
- qu'une participation à un concours est autorisée sans vérifier ses règles;
- qu'une solution peut être publiée ou soumise automatiquement.
