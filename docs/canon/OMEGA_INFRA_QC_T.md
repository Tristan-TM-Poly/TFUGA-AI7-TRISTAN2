# Ω-INFRA-QC-T / InfrastructureGraph Quebec

Status: B/C — canon + MVP direction
Date: 2026-07-06
Owner: Tristan Jean Joseph Dominic Tardif-Morency

## 0. Phrase-mère

```text
Cartographier, comprendre, protéger, maintenir, réparer et améliorer
les infrastructures publiques, privées, critiques, municipales,
industrielles, numériques, énergétiques, sociales et territoriales du Québec
sans exposer des détails sensibles ou exploitables.
```

## 1. Définition

Ω-INFRA-QC-T est le système Tristan pour transformer l'infrastructure en hypergraphe vivant OAK-safe.

```text
InfrastructureGraph Québec = HGFM(
  actifs,
  propriétaires,
  opérateurs,
  usages,
  dépendances,
  risques,
  contrats,
  maintenance,
  climat,
  cybersécurité,
  communautés,
  coûts,
  preuves,
  résilience
)
```

## 2. Secteurs couverts

### Public

```text
écoles, cégeps, universités, hôpitaux, bâtiments publics, palais de justice,
centres administratifs, routes, ponts, aqueducs, égouts, parcs, bibliothèques,
centres sportifs, logements sociaux, centres de données publics.
```

### Privé

```text
télécommunications, centres de données, banques, assurances, logistique,
alimentation, usines, mines, pharmaceutique, immobilier commercial,
plateformes numériques, énergie privée.
```

### Mixte

```text
transport collectif, ports, aéroports, réseaux énergétiques, grands projets,
partenariats, réseaux de recharge, logistique alimentaire.
```

### Communautaire / territorial

```text
routes isolées, eau potable locale, communications d'urgence,
énergie hors réseau, transport médical, centres communautaires,
infrastructures culturelles et lieux de mémoire.
```

## 3. Garde-fou central

```text
Le système ne publie pas de vulnérabilités exploitables.
Il sépare information publique, information restreinte et information critique.
```

Ne jamais publier par défaut :

- emplacements sensibles exacts non publics ;
- configurations réseau ;
- chemins d'accès ;
- détails de sécurité physique ;
- plans d'urgence confidentiels ;
- données personnelles ;
- dépendances critiques exploitables ;
- informations qui faciliteraient sabotage, intrusion ou ciblage.

## 4. Noyau technique

```text
AssetNode
DependencyEdge
InfraGraph
SourceRegistry
EvidenceItem
InfraRiskTensor
MaintenanceSignal
ResilienceScenario
OAKSecurityGate
MarkdownReportFactory
```

## 5. Produits possibles

```text
Infra-OAK Audit Express
Municipal Resilience Map
Private Infra Risk Report
Quebec InfraGraph Dashboard
Procurement Integrity Lens
Climate-Maintenance Prioritizer
Critical Dependency Simulator
8e Feu Infrastructure Index
```

## 6. Règle OAK

```text
Voir les actifs.
Voir les dépendances.
Voir les risques.
Voir les preuves.
Agir avant la fracture.
```

## 7. Statut MVP

Le MVP doit commencer avec des données démo et des exemples fictifs ou autorisés.

```text
No real sensitive infrastructure exposure by default.
No remote fetch by default.
No final authority claim.
Human review required for real-world use.
```
