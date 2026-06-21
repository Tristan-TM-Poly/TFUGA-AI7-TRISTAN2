# Ω-SERVICES-QC-T / ServiceGraph-QC

Prototype OAK-safe pour diagnostiquer et améliorer les services publics québécois avec l'architecture de Tristan : HGFM + CVCD + OAK + Bayes-Tristan + mémoire négative M⁻ + ZERO-TOUCH.

## But

ServiceGraph-QC transforme un service public en hypergraphe opérationnel : citoyens, employés, lois, données, formulaires, systèmes, délais, erreurs, recours et confiance.

Le prototype vise à mesurer et réduire :

- friction citoyenne;
- délais réels de résolution;
- erreurs et blocages;
- opacité administrative;
- exclusion numérique;
- dépendance aux fournisseurs;
- absence de recours humain;
- risques de déploiement de type SAAQclic/CASA.

## Principe OAK-safe

Ce dépôt ne prétend pas automatiser l'État ni remplacer des employés publics. Il fournit un cadre de diagnostic, d'audit, de simulation et de conception de meilleurs parcours citoyens.

Règles strictes :

1. aucune décision sensible entièrement automatisée;
2. maintien d'un recours humain clair;
3. protection de la vie privée et minimisation des données;
4. accessibilité multicanal, pas seulement numérique;
5. cybersécurité et journalisation;
6. déploiement progressif, testable et réversible;
7. mémoire négative M⁻ pour ne pas répéter les fiascos.

## Structure

```text
servicegraph_qc/
  README.md
  service_model.yaml
  m_minus_registry.yaml
  oak_service_meter.py
  friction_map.py
  examples/
    saaq_renew_license.yaml
    ramq_health_card.yaml
    revenu_quebec_notice.yaml
    education_financial_aid.yaml
  reports/
    reform_blueprint_qc.md
```

## Utilisation rapide

```bash
python servicegraph_qc/oak_service_meter.py servicegraph_qc/examples/saaq_renew_license.yaml
python servicegraph_qc/friction_map.py servicegraph_qc/examples/saaq_renew_license.yaml
```

Les scripts utilisent seulement la bibliothèque standard Python.

## Formule mère

```text
Service_QC+ = besoin_resolu - friction - delai - erreur - opacite - humiliation + confiance + recours + accessibilite
```

## État visé

Un service public québécois doit devenir clair, humain, accessible, mesurable, cyber-sécuritaire, souverain numériquement et capable d'apprendre de ses échecs.
