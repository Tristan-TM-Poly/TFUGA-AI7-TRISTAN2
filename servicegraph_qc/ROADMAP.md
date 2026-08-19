# ServiceGraph-QC Roadmap

## Vision

Transformer Omega-Services-QC-T en moteur de diagnostic et d'amélioration continue des services publics québécois.

## Phase 0 — MVP actuel

- Modèle `service_model.yaml`.
- Registre de mémoire négative anti-répétition.
- Scripts `oak_service_meter.py`, `friction_map.py`, `batch_oak_report.py`.
- Exemples initiaux : SAAQ, RAMQ, Revenu Québec, aide financière aux études, justice, immigration et francisation, permis municipal, services aux entreprises.
- Tests unitaires et GitHub Actions.

## Phase 1 — Atlas de 20 services

Ajouter dix à douze parcours supplémentaires dans les domaines santé, éducation, travail, municipalités, mobilité, retraite, énergie, services régionaux et changement d'adresse.

Livrables :

```text
20 fichiers YAML
20 cartes de friction
1 rapport batch comparatif
1 registre anti-erreurs enrichi
```

## Phase 2 — Indicateurs avancés

Ajouter :

- score de risque de lancement;
- score d'exclusion numérique;
- score de dépendance fournisseur;
- score de dette formulaire;
- score de clarté citoyenne;
- estimateur de gain si une friction est corrigée.

## Phase 3 — Générateur de recommandations

Transformer les frictions en plans d'action structurés :

```text
friction -> cause racine -> test OAK -> correctif -> métrique -> risque résiduel
```

## Phase 4 — Dashboard local

Créer une interface locale statique :

- tableau des scores;
- filtres par organisme;
- carte de friction;
- principales pénalités;
- tests OAK manquants;
- fiche de réforme par service.

## Phase 5 — Civic-AIT-QC

Prototype d'assistant d'orientation public OAK-safe :

- réponses sourcées;
- aucune décision administrative autonome;
- explication en français clair;
- checklist personnalisable;
- escalade humaine;
- journalisation des incertitudes.

## Phase 6 — Institutionnalisation

Proposer :

- OAKGate gouvernemental;
- laboratoire citoyen et employés;
- registre inter-organismes anti-erreurs;
- composantes numériques communes;
- exigences contractuelles anti-verrouillage;
- tableau public de délai et résolution.

## Définition de réussite

Le projet réussit si chaque nouveau service modélisé réduit au moins un des éléments suivants sans réduire sécurité, équité ou recours humain :

- nombre d'étapes;
- nombre de documents;
- nombre de contacts;
- délai médian;
- opacité de statut;
- taux d'abandon;
- correction tardive;
- exclusion numérique;
- dépendance externe critique.
