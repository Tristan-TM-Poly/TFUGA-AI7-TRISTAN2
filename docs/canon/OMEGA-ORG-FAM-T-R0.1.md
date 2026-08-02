# Ω-ORG-FAM-T R0.1 — Familles de molécules organiques de Tristan

## Statut

Architecture computationnelle OAK-safe. Les taxonomies et règles chimiques établies servent de socle; les cellules combinatoires générées sont des hypothèses de classification, pas des molécules prouvées.

## Noyau

Une famille moléculaire est une région d'un espace à six axes : squelette, famille fonctionnelle, classe électronique, archétype réactionnel, stéréochimie et environnement physicochimique. Chaque cellule possède des marqueurs spectraux, des contradictions, trois gabarits de preuve et un statut OAK.

## Première matérialisation massive

- 262 144 cellules familiales;
- 786 432 gabarits de preuve et de contrôle négatif;
- 1 048 576 objets liés;
- compression JSONL+gzip déterministe;
- génération en streaming;
- aucune limite permanente sur le nombre total d'objets.

`--family-records` définit seulement une expérience finie. Ce paramètre n'est pas un plafond architectural. Pour dépasser 262 144, le moteur continue en espaces nommés; une version scientifique ultérieure devra surtout étendre les vocabulaires révisés et les données expérimentales plutôt que compter des duplications comme découvertes.

## OAK

Le volume n'est pas une densité de preuve. Une cellule ne certifie ni existence moléculaire, ni stabilité, ni synthétisabilité, ni identité analytique, ni sécurité. Toute promotion exige plusieurs modalités indépendantes, des contre-exemples, des données de référence, des incertitudes et un domaine de validité.

## Commandes

```bash
omega-organic-family generate --family-records 262144
omega-organic-family classify alcohol_phenol "O-H environment" oxidation_reduction
omega-organic-family audit generated/omega_org_fam_t_r01
```

## Frontières suivantes

1. registre extensible chargé depuis JSON/YAML;
2. intégration RDKit optionnelle et validation de valence;
3. signatures Raman/FTIR/RMN/MS avec provenance;
4. graphe réactionnel atomiquement équilibré;
5. détection de mélanges et déconvolution symbolique;
6. backpressure adaptatif relié à Ω-SANS-PLAFOND-T∞;
7. sharding distribué et reprise par checkpoints;
8. échantillonnage OAK stratifié pour millions d'objets.
