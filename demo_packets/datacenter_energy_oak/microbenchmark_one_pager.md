# Microbenchmark OAK — Optimisation thermique / énergétique de datacenter

## Résumé

Je propose un microbenchmark OAK-safe de 2 à 4 semaines pour tester un framework prototype d’IA scientifique et de décision prudente appliqué à un cas datacenter : énergie, refroidissement, risque de hotspots, contrôle, ROI et limites.

Le but n’est pas de vendre une solution validée industriellement. Le but est de **tester**, **mesurer**, **falsifier** et **documenter** une méthode sur un cas simple, auditable et reproductible.

## Entrées possibles

- modèle thermique simplifié;
- données simulées;
- données anonymisées non sensibles;
- scénario de contrôle énergétique;
- hypothèse de réduction de refroidissement;
- cas pédagogique fourni par un laboratoire ou une équipe de recherche.

## Sorties prévues

- baseline énergétique / thermique;
- PUE proxy ou métrique équivalente;
- estimation prudente de réduction de refroidissement;
- score de risque hotspot;
- décomposition des résidus;
- vérification d’invariants;
- estimation ROI-OAK avec probabilité de vérification;
- décision : recherche seulement / candidat pilote / no-go M−.

## Méthode

```text
Baseline
→ scénario optimisé
→ métriques thermiques et énergétiques
→ résidus
→ invariants
→ ROI-OAK
→ rapport limites / risques / prochaine étape
```

## Ce qui est déjà disponible

Le dépôt contient déjà un MVP logiciel :

```text
omega_vtp_t/datacenter_thermal.py
examples/datacenter_oak_demo.py
```

Le code produit un rapport avec :

- PUE proxy baseline;
- PUE proxy optimisé;
- réduction de PUE;
- réduction du risque hotspot;
- valeur annuelle attendue;
- statut OAK thermique;
- décision financière;
- décision unifiée.

## Limites explicites

- Ne remplace pas une simulation CFD.
- Ne remplace pas une instrumentation réelle.
- Ne remplace pas l’expertise facility/datacenter.
- Ne prétend pas valider un rendement industriel.
- Les économies estimées sont hypothétiques tant qu’elles ne sont pas vérifiées sur données réelles ou pilote encadré.

## Demande de collaboration

Format léger proposé :

1. choisir un cas test simple;
2. définir une baseline;
3. exécuter ou adapter le microbenchmark;
4. produire un rapport OAK;
5. décider : abandon, amélioration, mini-projet, stage, prototype ou pilote.

## Valeur pour une université

- cas concret d’IA scientifique et énergie;
- support pour étudiants/projets de recherche;
- cadre clair de validation/falsification;
- pont entre simulation, optimisation, économie et transfert technologique;
- base possible pour publication, prototype ou partenariat industriel.
