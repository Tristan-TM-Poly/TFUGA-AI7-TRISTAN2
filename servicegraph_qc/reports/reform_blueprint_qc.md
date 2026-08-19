# Ω-SERVICES-QC-T — Blueprint de réforme des services publics québécois

## Mission

Créer un cadre reproductible pour améliorer les services québécois : SAAQ, RAMQ, Revenu Québec, aide financière aux études, justice, immigration, municipalités, santé, transport et services aux entreprises.

La réforme ne doit pas être seulement une numérisation. Elle doit réduire la friction réelle entre un besoin humain et sa résolution.

## Formule mère

```text
Service_QC+ = besoin_resolu - friction - delai - erreur - opacite - humiliation + confiance + recours + accessibilite
```

## Architecture

1. **ServiceGraph** : cartographier le parcours de bout en bout.
2. **FrictionMap** : détecter clics, appels, preuves, déplacements, attentes, incompréhensions et stress.
3. **OAK-ServiceMeter** : scorer résolution, accessibilité, transparence, sécurité, recours humain, interopérabilité et coûts.
4. **M⁻ Registry** : convertir chaque fiasco en règle anti-répétition.
5. **OAKGate** : bloquer tout lancement massif sans preuve opérationnelle.
6. **Civic-AIT-QC** : assistant d'orientation sourcé, jamais décision opaque autonome.

## Lois opérationnelles

### 1. Le citoyen ne porte pas la complexité interne

L'État doit orchestrer ses ministères et organismes derrière une interface compréhensible.

### 2. Numérique par défaut, humain garanti

Le numérique accélère, mais ne remplace pas téléphone, comptoir, accompagnement et recours.

### 3. Chaque formulaire est une dette de design

Un formulaire long ou répétitif signale une intégration interne insuffisante.

### 4. Chaque délai est un indicateur de gouvernance

Les délais doivent être publics, mesurés et associés à des seuils d'escalade.

### 5. Aucun déploiement critique sans OAKGate

Pas de lancement massif sans tests citoyens, employés, charge, panne, cybersécurité, accessibilité et retour arrière.

### 6. L'État doit posséder son architecture critique

Les fournisseurs peuvent aider, mais l'État doit conserver architecture, données, documentation, décisions et capacité d'audit.

### 7. Les employés publics sont des capteurs de vérité

Les agents voient les exceptions, irritants, contournements et erreurs. Le système doit capter leur intelligence pratique.

### 8. L'IA publique explique et oriente; elle ne juge pas seule

Pour santé, justice, fiscalité, immigration, aide sociale et permis, toute décision sensible doit garder explication, humain responsable et appel.

## Roadmap MVP

### Phase 1 — Cartographie

- sélectionner 20 services douloureux;
- créer un fichier ServiceGraph par service;
- identifier segments citoyens vulnérables;
- documenter frictions, risques et recours.

### Phase 2 — Mesure

- exécuter `oak_service_meter.py` sur chaque service;
- comparer scores et pénalités;
- produire un tableau de priorisation.

### Phase 3 — Réduction de friction

- utiliser `friction_map.py`;
- transformer chaque friction en action;
- inscrire les échecs dans M⁻.

### Phase 4 — Déploiement prudent

- pilote limité;
- mesure publique;
- correction;
- expansion graduelle;
- mode dégradé permanent.

## Critères d'une réforme réussie

- moins d'étapes citoyennes;
- moins de documents redemandés;
- délais visibles et plus courts;
- statut de demande clair;
- recours humain disponible;
- moins de dépendance fournisseur;
- meilleure accessibilité;
- cybersécurité maintenue;
- coûts et risques transparents;
- mémoire négative institutionnelle vivante.

## Sortie attendue

Un Québec administratif plus clair, plus rapide, plus humain, plus francophone, plus accessible, plus souverain numériquement et capable d'apprendre de ses erreurs.
