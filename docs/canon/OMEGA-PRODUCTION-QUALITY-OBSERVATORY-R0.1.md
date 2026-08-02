# Ω-PRODUCTION-QUALITY-OBSERVATORY-T R0.1

## Production, qualité, preuve externe et conversion en actifs

**Statut :** observatoire déterministe et OAK-safe de la production du dépôt. Il mesure des preuves visibles dans un périmètre donné; il ne certifie ni vérité scientifique, ni nouveauté, ni valeur économique.

## 1. Pourquoi cet observatoire existe

Le dépôt a dépassé le stade où le problème principal était la quantité. Il sait maintenant produire, matérialiser, exécuter, reprendre, partitionner, hacher, auditer et fusionner des systèmes à très grande échelle.

Le nouveau risque est la confusion suivante :

```text
adresse virtuelle
≠ plan
≠ objet matérialisé
≠ workload synthétique exécuté
≠ résultat scientifique externe
≠ produit adopté
≠ revenu
```

Ω-PRODUCTION-QUALITY-OBSERVATORY-T rend ces classes non interchangeables.

## 2. Snapshot du 2 août 2026

Périmètre : PR `#229` à `#258`, soit 30 PR inspectées.

```yaml
merged_pull_requests: 21
open_pull_requests: 8
closed_unmerged_or_superseded: 1
merged_pr_commit_associations: 505
open_pr_commit_associations: 111
global_python_compile_observed_success: true
global_pytest_observed_success: true
```

Les associations de commits ne mesurent pas directement l'effort net : elles incluent synchronisations, corrections CI et commits générés. Elles restent utiles pour détecter la dette de travail en cours.

## 3. Volume réel démontré

L'indicateur conservateur additionne seulement le plus grand front non supersédé de cinq lignées majeures :

| Lignée | Front démontré | Classe |
|---|---:|---|
| Ω-ORG-FAM-T | 67 108 864 | objets de recherche matérialisés |
| Ω-NARUTO-HMAGFM-HGFMnD² | 10 000 000 | records déterministes exécutés et revérifiés |
| Ω-DISCOVERY-KERNEL-T∞ | 4 000 000 | événements exécutés avec interruption et reprise |
| Ω-GENERATOR-DISCOVERY R0.3 Ultra | 393 216 | records liés matérialisés et indexés |
| Ω-SANS-PLAFOND-T∞ | 100 000 | ajouts logiques compilés en dry-run GitHub |
| **Indicateur minimal** | **81 602 080** | unités hétérogènes, non scientifiques |

Cette somme prouve une capacité de production informatique. Elle ne représente pas 81,6 millions de découvertes, d'expériences, de molécules, d'utilisateurs ou de dollars.

## 4. Échelles à ne pas ajouter au volume réel

| Échelle | Valeur | Classe correcte |
|---|---:|---|
| Atlas organique adressable | 68 719 476 736 | espace logique non entièrement matérialisé |
| Projection Discovery | 9 437 184 000 | capacité planifiée non exécutée |
| Frontier Generator R0.5 | 1 000 000 000 000 000 | plan virtuel analytique O(1) |

Un quadrillion virtuel peut démontrer l'efficacité d'un codec, d'un scheduler ou d'un planificateur. Il ne doit jamais satisfaire une gate d'exécution.

## 5. Vecteur de qualité heuristique

Ces valeurs sont des aides de navigation, pas des probabilités de vérité et pas une autorité de promotion.

| Dimension | Score / 10 | Lecture |
|---|---:|---|
| Capacité d'échelle | 10.0 | Le volume n'est plus le goulot |
| Reproductibilité d'ingénierie | 9.2 | IDs, hashes, Merkle, manifests, reprise |
| Qualité des modules ciblés | 8.8 | CLIs, schémas, tests et contrats typés |
| Discipline OAK | 9.3 | Non-claims, mémoire M⁻ et frontières explicites |
| Réversibilité et récupération | 9.0 | checkpoints, dry-runs, canaris et rollback |
| Intégration du monorepo | 8.0 | compilation et pytest global observés verts |
| Maintenabilité | 5.8 | forte croissance d'artefacts et workflows |
| Concentration stratégique | 4.5 | trop de fronts peuvent rester ouverts simultanément |
| Validation scientifique externe | 2.5 | peu de données instrumentales et réplications externes observées |
| Validation produit externe | 2.0 | peu d'utilisateurs ou pilotes externes confirmés dans le périmètre |
| Validation de revenu | 1.0 | aucune preuve confirmée dans le périmètre inspecté |

## 6. Gates exécutables

### Volume

Vert lorsque :

- au moins un million d'unités ont réellement été matérialisées ou exécutées;
- les plans virtuels restent explicitement exclus du nombre réel.

### Intégration

Vert lorsque compilation Python globale et pytest global sont observés verts sur une autorité GitHub récente.

### WIP

Vert lorsque :

```yaml
open_pull_requests <= 5
open_pr_commit_associations <= 60
```

Le snapshot actuel contient 8 PR ouvertes et 111 associations de commits : la gate est rouge.

### Science externe

Vert lorsqu'au moins un signal confirmé existe :

- dataset instrumental réel avec provenance;
- réplication indépendante;
- revue externe par expert du domaine.

### Produit externe

Vert lorsqu'au moins un signal confirmé existe :

- utilisateur actif externe;
- pilote externe;
- événement de revenu confirmé.

## 7. Décision R0.1

```text
REDUCE_WIP_AND_EXTERNALIZE
```

La décision n'est pas « arrêter de créer ». Elle signifie :

1. réduire les fronts simultanés;
2. transformer les meilleurs systèmes fusionnés en expériences externes;
3. capturer les résultats négatifs;
4. mesurer la valeur avant/après;
5. n'autoriser une nouvelle expansion massive que lorsqu'elle sert une preuve externe précise.

## 8. Trois méta-produits actifs

### A. OAKGate / Audit Express

Entrée : dépôt, PR, claims, preuves et CI.

Sortie : rapport de risques, dette de preuve, corrections prioritaires, règles CI et dossier avant/après.

Preuve externe cible : trois audits sur des dépôts externes avec temps économisé, défauts détectés et faux positifs mesurés.

### B. HyperKnowledge / Absorption Engine

Entrée : corpus documentaire ou scientifique autorisé.

Sortie : claims atomiques, provenance, contradictions, tests manquants et file d'actions.

Preuve externe cible : trois corpus externes, avec évaluation humaine de précision, rappel et utilité des actions.

### C. Discovery Benchmark Service

Entrée : méthode scientifique ou algorithme candidat.

Sortie : baseline, contrôles négatifs, holdout, stress tests, résidus et paquet reproductible.

Preuve externe cible : trois méthodes sur données publiques réelles, comparées à des baselines reconnues.

## 9. Règle de conversion

Toute nouvelle branche massive doit déclarer avant exécution :

```yaml
external_question: required
external_dataset_or_user: required
baseline: required
measured_outcome: required
falsification_condition: required
rollback_or_exit: required
```

Une exception peut être accordée pour infrastructure critique, correction de sécurité ou consolidation, avec justification OAK explicite.

## 10. M⁻ prioritaire

```text
Ne jamais utiliser la plus grande cardinalité disponible comme résumé principal de la valeur du dépôt.
```

Correction : toujours publier au minimum les six classes de volume, la source de preuve, le statut externe, le coût et les non-claims.

## 11. Commande

```bash
python tools/production_quality_observatory.py \
  --snapshot reports/production_quality_snapshot_2026-08-02.json \
  --policy policies/omega_production_quality_observatory_r0_1.json \
  --output-json generated/production-quality/report.json \
  --output-md generated/production-quality/report.md
```

## 12. Frontière OAK

L'observatoire mesure ce qui est documenté dans son snapshot. Un zéro externe signifie « aucune confirmation observée dans ce périmètre », pas « absence absolue ». Les scores heuristiques ne doivent jamais devenir une certification automatique. La publication, la promotion scientifique, les décisions juridiques, l'IP, la sécurité et les revendications commerciales restent humaines et contextualisées.
