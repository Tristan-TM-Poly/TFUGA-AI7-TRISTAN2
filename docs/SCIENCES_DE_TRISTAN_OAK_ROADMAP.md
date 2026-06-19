# Roadmap OAK — Sciences de Tristan

Cette feuille de route convertit le manifeste Ω-ST en travail testable. Chaque axe doit produire un artefact, une baseline, une métrique et une mémoire négative.

## Phase 0 — Stabiliser le noyau canonique

**Objectif :** transformer les Sciences de Tristan en objet stable dans le dépôt.

Livrables :

- `docs/SCIENCES_DE_TRISTAN.md`
- `schemas/science_card.schema.json`
- `examples/sciences_tristan_seed.yaml`
- une matrice de priorisation Bayes-Tristan
- une liste de tests OAK minimaux

Critère de sortie :

```text
Toute nouvelle idée peut être représentée comme science_card + status_oak + next_action.
```

## Phase 1 — Bayes-Tristan Engine

**But :** classer les hypothèses selon vérité, utilité, fertilité, testabilité, sécurité, compressibilité, nouveauté et valeur.

Entrées :

- cartes YAML `science_card`
- résultats OAK
- mémoire positive et négative
- coûts et contraintes

Sorties :

- score de priorité
- statut recommandé
- prochain test optimal
- raison de promotion ou de blocage

Métrique minimale :

```text
Le système doit trier au moins 20 hypothèses en une liste priorisée justifiée.
```

## Phase 2 — AIT-OAK

**But :** créer un agent critique qui transforme une hypothèse en protocole de validation.

Pour chaque hypothèse, AIT-OAK doit produire :

- version forte de l'énoncé ;
- version prudente ;
- hypothèses nécessaires ;
- contre-exemples candidats ;
- baselines ;
- métriques ;
- conditions de réfutation ;
- statut OAK ;
- prochaine action.

Critère de sortie :

```text
Aucune hypothèse Omega_2+ ne reste sans test ou limite explicite.
```

## Phase 3 — FFWT-HAC-CVCD

**But :** tester la branche signal la plus immédiatement mesurable.

Pipeline :

```text
signal -> FFWT -> covariance/corrélation/cohérence -> features CVCD -> modèle -> baseline -> rapport OAK
```

Baselines :

- FFT
- ondelettes classiques
- STFT
- PCA/SVD
- features statistiques simples

Tâches :

- classification synthétique multi-échelles ;
- détection d'anomalies ;
- robustesse au bruit ;
- compression ou reconstruction ;
- spectres matériaux si disponibles.

Critère de promotion :

```text
FFWT-HAC-CVCD doit améliorer au moins une métrique claire par rapport à une baseline pertinente.
```

## Phase 4 — Fractal RLC Lab

**But :** tester les géométries fractales conductrices comme réseaux résonants simulables.

Objets :

- graphe régulier ;
- graphe aléatoire ;
- Sierpinski ;
- cube triadique troué ;
- HGFM simplifié ;
- réseau hybride conducteur/magnétique.

Mesures :

- fréquences propres ;
- facteur Q ;
- réponse en fréquence ;
- localisation des modes ;
- bandes interdites ;
- robustesse aux défauts.

Règle OAK :

```text
Modes résonants/topologiques possibles ≠ supraconductivité prouvée.
```

Pour parler de supraconductivité, il faudra des critères expérimentaux : résistance nulle, effet Meissner, gap, cohérence de phase et reproductibilité.

## Phase 5 — Materials CVCD Scanner

**But :** relier les Sciences de Tristan au génie physique.

Entrées :

- spectres Raman ;
- XRD ;
- IR ;
- signaux de transport ;
- images microscopiques ;
- données simulées.

Sorties :

- pics et largeurs ;
- anomalies ;
- signatures multi-échelles ;
- hypothèses de phase ;
- tests suggérés ;
- statut OAK.

Critère de promotion :

```text
Le scanner doit retrouver des signatures connues sur des données de référence avant de promouvoir des signatures nouvelles.
```

## Phase 6 — HGFM Corpus Mapper

**But :** transformer le corpus en hypergraphe vivant.

Nœuds :

- idées ;
- équations ;
- documents ;
- prototypes ;
- agents ;
- erreurs ;
- tests ;
- résultats ;
- branches.

Hyperarêtes :

- inspire ;
- formalise ;
- teste ;
- réfute ;
- compresse ;
- étend ;
- canonise ;
- produit.

Critère de promotion :

```text
Le graphe doit permettre d'extraire au moins 10 synergies nouvelles avec statut OAK et prochaine action.
```

## Phase 7 — Negative Memory Engine

**But :** convertir chaque erreur en anti-règle réutilisable.

Exemple :

```yaml
anti_rule:
  name: no_material_claim_without_measurement
  trigger: "claim implies a material property"
  required_checks:
    - units
    - mechanism
    - baseline
    - measurable prediction
    - falsifier
```

Critère de promotion :

```text
Réduire la répétition d'erreurs dans les nouvelles fiches hypothèses.
```

## Phase 8 — Theory-to-Paper

**But :** convertir les branches validées en articles, rapports ou livres.

Entrée :

- fiche théorie ;
- statut OAK ;
- prototypes ;
- résultats ;
- limites ;
- figures ;
- bibliographie à compléter.

Sortie :

- abstract ;
- introduction ;
- méthode ;
- expériences ;
- limites ;
- conclusion ;
- checklist OAK.

Critère de promotion :

```text
Un module Omega_4+ doit pouvoir générer un manuscrit technique minimal.
```

## Matrice de priorité initiale

| Projet | Testabilité | Fertilité | Utilité | Statut initial |
|---|---:|---:|---:|---|
| FFWT-HAC-CVCD | 0.90 | 0.95 | 0.85 | Omega_2 |
| Bayes-Tristan Engine | 0.80 | 0.95 | 0.90 | Omega_2 |
| AIT-OAK | 0.85 | 0.90 | 0.95 | Omega_2 |
| Fractal RLC Lab | 0.85 | 0.85 | 0.75 | Omega_2 |
| Materials CVCD Scanner | 0.80 | 0.90 | 0.85 | Omega_2 |
| HGFM Corpus Mapper | 0.70 | 0.95 | 0.90 | Omega_1 |
| Negative Memory Engine | 0.75 | 0.85 | 0.95 | Omega_1 |
| Theory-to-Paper | 0.70 | 0.80 | 0.90 | Omega_1 |

## Definition of done globale

Une branche passe de graine à science opérationnelle si elle possède :

1. une fiche canonique ;
2. un statut OAK ;
3. une baseline ;
4. une métrique ;
5. un prototype minimal ;
6. un résultat ou un résidu ;
7. une mémoire positive ou négative ;
8. une prochaine action.
