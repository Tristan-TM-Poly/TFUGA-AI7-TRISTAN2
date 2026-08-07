# Spécification des campagnes multi-dépôts

## Unité de travail

La campagne, et non nécessairement la PR isolée, devient l’unité de transformation.

```text
Campaign
├── intention
├── création racine
├── snapshot source
├── artefacts
├── routes
├── PR plans
├── dépendances
├── OAK findings
├── EvidenceBundle
├── rollback
└── canon update proposal
```

## Invariants

1. Chaque PR plan possède un dépôt, une base et une branche de tête uniques.
2. Chaque PR reste `draft=true`.
3. `human_gate_required=true` pour chaque PR.
4. `remote_action_planned=false` dans R0.1.
5. Toute dépendance inter-PR doit pointer vers un autre plan de la campagne.
6. Le graphe de dépendance doit être acyclique.
7. Chaque chemin modifié doit être préannoncé dans `allowed_paths`.
8. Chaque PR possède une hypothèse et une cour de vérification attendue.
9. Le rollback est obligatoire.
10. Aucun plafond permanent global du nombre de PR n’est encodé; chaque exécution reste toutefois finie.

## Campagnes empilées

Un portefeuille GitHub peut déjà contenir des PR empilées sur des branches de fonctionnalités. Le scanner conserve `base_branch` et `head_branch`; une version future calculera automatiquement les dépendances depuis les bases non principales et les mentions explicites.

R0.1 ne prétend pas résoudre automatiquement tous les empilements historiques. Il rend leur modélisation possible et échoue fermée lorsqu’une dépendance déclarée est cyclique ou inconnue.

## États

```text
PLANNED
SCAFFOLDED
CODE_GENERATED
LOCALLY_TESTED
PRS_OPEN
CI_RUNNING
PARTIALLY_BLOCKED
OAK_REVIEW
READY
MERGED
ROLLED_BACK
CANONIZED
```

R0.1 matérialise uniquement `PLANNED`.

## Passage à une mutation future

Une couche ultérieure peut convertir les plans en branches et PR brouillons seulement après :

- snapshot frais;
- head exact;
- autorisation explicite de Tristan;
- vérification IP et visibilité;
- paths allowlist;
- rollback;
- tests locaux;
- absence de conflits avec une campagne concurrente;
- preuve que la PR correspond toujours au plan revu.

La fusion demeure une action distincte, jamais implicite dans l’autorisation de créer une branche ou une PR.
