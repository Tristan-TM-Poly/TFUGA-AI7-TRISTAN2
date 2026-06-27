# GitHubRealmEngine-T — OMEGA-GAME-T+++

`GitHubRealmEngine-T` transforme un depot en carte jouable de maintenance.

Il prolonge GameEngineOS-T :

```text
RepoWorld -> GitHubRealmEngine -> Quest -> Score -> Better Repo
```

## Role

GitHubRealmEngine represente un depot comme un monde : zones, quetes, gates, dette technique, qualite documentaire, qualite de tests et memoire M+/M-.

Le moteur est un simulateur interne. Il produit des recommandations et des scores, sans effectuer d'action distante.

## Carte du depot

```text
repo
├── docs zone
├── code zone
├── tests zone
├── schemas zone
├── examples zone
├── ci tower
└── review path
```

## Quetes MVP

- `add_missing_tests` ;
- `update_readme_map` ;
- `add_schema_for_new_output` ;
- `reduce_large_pr_risk` ;
- `prepare_oak_review`.

## Score

```text
RepoScore = tests + docs + schemas + examples + ci + oak - risk - drift - oversized_change
```

## Bosses symboliques

- missing tests ;
- outdated README ;
- missing schema ;
- unclear demo ;
- large change set ;
- weak OAK gate.

## Regles OAK

- simulation only ;
- recommendations only ;
- limits visible ;
- human review for repository changes ;
- M+ and M- recorded.

## Extension prevue

- IssueQuest generator ;
- review path maps ;
- CI tower scores ;
- repo atlas ;
- maintenance heatmap ;
- GameMaster Academy for RepoGM, TestGM, DocsGM and ReleaseGM.
